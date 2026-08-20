import json
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import stripe
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils.decorators import method_decorator
from django.utils import timezone as dj_timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from thefood.models import Customer, Order, OrderItem, Product

from .models import StripeCustomer, StripeWebhookEvent, Subscription, SubscriptionItem
from .serializers import SubscriptionStartSerializer

SHIPPING_PRICE_SETTINGS = {
    'weekly': 'STRIPE_SHIPPING_PRICE_ID_WEEKLY',
    'biweekly': 'STRIPE_SHIPPING_PRICE_ID_BIWEEKLY',
    'monthly': 'STRIPE_SHIPPING_PRICE_ID_MONTHLY',
}

# Must match the interval/interval_count of the corresponding shipping price
# in Stripe, since all items on a Subscription share one billing schedule.
RECURRING_BY_FREQUENCY = {
    'weekly': {'interval': 'week', 'interval_count': 1},
    'biweekly': {'interval': 'week', 'interval_count': 2},
    'monthly': {'interval': 'month', 'interval_count': 1},
}

# https://docs.stripe.com/tax/tax-codes.md — "Food for non-immediate consumption"
FOOD_TAX_CODE = 'txcd_40040000'

ACTIVE_SUBSCRIPTION_STATUSES = ('incomplete', 'active', 'past_due', 'paused')


def _next_delivery_date(frequency, from_date=None):
    from_date = from_date or date.today()
    if frequency == 'weekly':
        return from_date + timedelta(days=7)
    if frequency == 'biweekly':
        return from_date + timedelta(days=14)
    if frequency == 'monthly':
        month = from_date.month + 1
        year = from_date.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        day = min(from_date.day, monthrange(year, month)[1])
        return date(year, month, day)
    raise ValueError(f"Unknown frequency: {frequency}")


class SubscriptionStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubscriptionStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        frequency = serializer.validated_data['frequency']
        requested_items = serializer.validated_data['items']

        shipping_price_id = getattr(settings, SHIPPING_PRICE_SETTINGS[frequency], None)
        if not shipping_price_id:
            return Response(
                {'detail': f"No Stripe shipping price configured for frequency '{frequency}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product_ids = [item['product_id'] for item in requested_items]
        products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}

        missing_ids = set(product_ids) - set(products.keys())
        if missing_ids:
            return Response(
                {'detail': f"Product(s) not found: {sorted(missing_ids)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ineligible = [p.title for p in products.values() if not p.is_subscription_eligible]
        if ineligible:
            return Response(
                {'detail': f"Product(s) not eligible for subscription: {', '.join(ineligible)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        partner_store_ids = {p.partner_store_id for p in products.values()}
        if len(partner_store_ids) > 1:
            return Response(
                {'detail': "All items in a subscription must come from a single partner store."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        partner_store = next(iter(products.values())).partner_store

        try:
            customer_profile = request.user.customer
        except Customer.DoesNotExist:
            return Response(
                {'detail': "Please complete your delivery address before starting a subscription."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Subscription.objects.filter(
            user=request.user, status__in=ACTIVE_SUBSCRIPTION_STATUSES
        ).exists():
            return Response(
                {'detail': "You already have an active subscription."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        box_total = sum(
            products[item['product_id']].price * item['quantity'] for item in requested_items
        )
        box_total_cents = round(box_total * 100)

        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe_address = {
            'line1': customer_profile.shipping_address,
            'city': customer_profile.city,
            'postal_code': customer_profile.postal_code,
            'country': customer_profile.country,
        }

        stripe_customer = StripeCustomer.objects.filter(user=request.user).first()
        try:
            if stripe_customer is None:
                stripe_customer_obj = stripe.Customer.create(
                    email=request.user.email,
                    name=customer_profile.full_name,
                    phone=customer_profile.phone,
                    address=stripe_address,
                    shipping={
                        'name': customer_profile.full_name,
                        'phone': customer_profile.phone,
                        'address': stripe_address,
                    },
                )
                stripe_customer = StripeCustomer.objects.create(
                    user=request.user, stripe_customer_id=stripe_customer_obj.id
                )
            else:
                # Refresh address on the existing Customer object so Stripe Tax
                # calculates against the customer's current delivery address.
                stripe.Customer.modify(
                    stripe_customer.stripe_customer_id,
                    name=customer_profile.full_name,
                    phone=customer_profile.phone,
                    address=stripe_address,
                )

            # Subscription items' price_data only accepts an existing Product ID
            # (unlike Checkout Session / Invoice Item price_data, which allow
            # inline product_data), so the box Product must be created first.
            # Cached per partner store so repeated subscriptions reuse one
            # Product instead of littering the Stripe dashboard with dupes.
            if partner_store.stripe_subscription_product_id:
                box_product_id = partner_store.stripe_subscription_product_id
            else:
                box_product = stripe.Product.create(
                    name=f'{partner_store.store_name} Subscription Box',
                    tax_code=FOOD_TAX_CODE,
                )
                box_product_id = box_product.id
                partner_store.stripe_subscription_product_id = box_product_id
                partner_store.save(update_fields=['stripe_subscription_product_id'])

            stripe_subscription = stripe.Subscription.create(
                customer=stripe_customer.stripe_customer_id,
                items=[
                    {
                        'price_data': {
                            'currency': 'sek',
                            'product': box_product_id,
                            'unit_amount': box_total_cents,
                            'recurring': RECURRING_BY_FREQUENCY[frequency],
                        },
                        'quantity': 1,
                    },
                    {'price': shipping_price_id, 'quantity': 1},
                ],
                payment_behavior='default_incomplete',
                payment_settings={'save_default_payment_method': 'on_subscription'},
                automatic_tax={'enabled': True},
                expand=['latest_invoice.confirmation_secret', 'pending_setup_intent'],
                metadata={
                    'django_user_id': str(request.user.id),
                    'partner_store_id': str(partner_store.id),
                },
            )
        except stripe.StripeError as e:
            return Response(
                {'detail': f"Stripe error: {getattr(e, 'user_message', None) or str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # stripe-python 15+ typed resources aren't dicts: .get() is disabled in
        # favor of attribute access (still supports [] item access, used below).
        # Invoice.payment_intent no longer exists (removed post-"Basil"); the
        # client_secret now comes from either pending_setup_intent (no payment
        # due yet, e.g. $0 first invoice) or latest_invoice.confirmation_secret
        # (payment due now) — the frontend must call stripe.confirmSetup vs
        # stripe.confirmPayment accordingly, hence the paired `type` field.
        pending_setup_intent = getattr(stripe_subscription, 'pending_setup_intent', None)
        if pending_setup_intent is not None:
            client_secret = getattr(pending_setup_intent, 'client_secret', None)
            payment_type = 'setup'
        else:
            latest_invoice = getattr(stripe_subscription, 'latest_invoice', None)
            confirmation_secret = getattr(latest_invoice, 'confirmation_secret', None) if latest_invoice else None
            client_secret = getattr(confirmation_secret, 'client_secret', None) if confirmation_secret else None
            payment_type = 'payment'

        subscription_items = stripe_subscription['items']['data']
        shipping_item = next(i for i in subscription_items if i['price']['id'] == shipping_price_id)
        box_item = next(i for i in subscription_items if i['id'] != shipping_item['id'])

        # current_period_end moved off the top-level Subscription and onto each
        # SubscriptionItem in the Basil API update (2025-03-31); both items
        # share one billing schedule, so either item's value works here.
        current_period_end = None
        period_end_ts = box_item['current_period_end']
        if period_end_ts:
            current_period_end = datetime.fromtimestamp(period_end_ts, tz=timezone.utc)

        with transaction.atomic():
            django_subscription = Subscription.objects.create(
                user=request.user,
                partner_store=partner_store,
                stripe_subscription_id=stripe_subscription.id,
                stripe_box_item_id=box_item['id'],
                stripe_shipping_item_id=shipping_item['id'],
                frequency=frequency,
                status='incomplete',
                full_name=customer_profile.full_name,
                phone=customer_profile.phone,
                shipping_address=customer_profile.shipping_address,
                city=customer_profile.city,
                postal_code=customer_profile.postal_code,
                country=customer_profile.country,
                current_period_end=current_period_end,
                next_delivery_date=_next_delivery_date(frequency),
            )
            for item in requested_items:
                SubscriptionItem.objects.create(
                    subscription=django_subscription,
                    product=products[item['product_id']],
                    quantity=item['quantity'],
                )

        return Response(
            {
                'subscription_id': django_subscription.id,
                'stripe_subscription_id': stripe_subscription.id,
                'status': django_subscription.status,
                'client_secret': client_secret,
                'type': payment_type,
            },
            status=status.HTTP_201_CREATED,
        )


# Stripe's subscription statuses don't line up 1:1 with STATUS_CHOICES.
# incomplete_expired (first invoice never paid, subscription auto-expired) and
# unpaid (renewal exhausted all retries) don't have their own local status;
# they're folded into the closest existing choice rather than adding new ones.
STRIPE_SUBSCRIPTION_STATUS_MAP = {
    'incomplete': 'incomplete',
    'incomplete_expired': 'canceled',
    'trialing': 'active',
    'active': 'active',
    'past_due': 'past_due',
    'canceled': 'canceled',
    'unpaid': 'past_due',
    'paused': 'paused',
}


def _invoice_stripe_subscription_id(invoice):
    # Basil-era Invoice: `subscription` was removed; the subscription now
    # lives under parent.subscription_details.subscription (confirmed against
    # a real invoice.payment_succeeded payload on API version
    # 2026-07-29.dahlia -- invoice['subscription'] is simply absent/None).
    parent = invoice.get('parent') or {}
    subscription_details = parent.get('subscription_details') or {}
    return subscription_details.get('subscription')


def _handle_subscription_updated(obj):
    stripe_subscription_id = obj.get('id')
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
    except Subscription.DoesNotExist:
        return

    # current_period_end moved off the top-level Subscription onto each
    # SubscriptionItem (same Basil-era change SubscriptionStartView already
    # works around) -- confirmed absent at top level on a real
    # customer.subscription.updated payload.
    current_period_end = subscription.current_period_end
    items = (obj.get('items') or {}).get('data') or []
    if items:
        period_end_ts = items[0].get('current_period_end')
        if period_end_ts:
            current_period_end = datetime.fromtimestamp(period_end_ts, tz=timezone.utc)

    new_status = STRIPE_SUBSCRIPTION_STATUS_MAP.get(obj.get('status'), subscription.status)

    subscription.status = new_status
    subscription.current_period_end = current_period_end
    subscription.save(update_fields=['status', 'current_period_end', 'updated_at'])


def _handle_subscription_deleted(obj):
    stripe_subscription_id = obj.get('id')
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
    except Subscription.DoesNotExist:
        return

    subscription.status = 'canceled'
    subscription.canceled_at = dj_timezone.now()
    subscription.save(update_fields=['status', 'canceled_at', 'updated_at'])


def _handle_invoice_payment_succeeded(obj):
    stripe_subscription_id = _invoice_stripe_subscription_id(obj)
    if not stripe_subscription_id:
        return  # one-off invoice, not tied to a subscription -- nothing to fulfill

    try:
        subscription = Subscription.objects.select_related('user').get(
            stripe_subscription_id=stripe_subscription_id
        )
    except Subscription.DoesNotExist:
        return

    items = list(subscription.items.select_related('product'))
    backorder_notes = []
    # amount_paid is what Stripe actually charged: box items + shipping +
    # tax. Summing product.price * quantity would silently drop the
    # shipping line item (and any tax) from the order total.
    total_amount = Decimal(obj.get('amount_paid') or 0) / 100

    with transaction.atomic():
        for item in items:
            product = item.product

            if product.stock_quantity is not None:
                if item.quantity > product.stock_quantity:
                    shortfall = item.quantity - product.stock_quantity
                    backorder_notes.append(f"Backorder: {product.title} short by {shortfall}")
                    product.stock_quantity = 0
                else:
                    product.stock_quantity -= item.quantity
                product.save(update_fields=['stock_quantity'])

        shipping_address = subscription.shipping_address
        if subscription.city or subscription.postal_code or subscription.country:
            shipping_address = (
                f"{subscription.shipping_address}\n"
                f"{subscription.city}, {subscription.postal_code}\n"
                f"{subscription.country}"
            )

        order = Order.objects.create(
            user=subscription.user,
            subscription=subscription,
            status='PENDING',
            total_amount=total_amount,
            full_name=subscription.full_name,
            phone=subscription.phone,
            shipping_address=shipping_address,
            delivery_date=subscription.next_delivery_date,
            notes='\n'.join(backorder_notes) or None,
        )

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price_at_purchase=item.product.price,
            )

        subscription.next_delivery_date = _next_delivery_date(
            subscription.frequency, from_date=subscription.next_delivery_date
        )
        subscription.save(update_fields=['next_delivery_date', 'updated_at'])


def _handle_invoice_payment_failed(obj):
    stripe_subscription_id = _invoice_stripe_subscription_id(obj)
    if not stripe_subscription_id:
        return

    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
    except Subscription.DoesNotExist:
        return

    subscription.status = 'past_due'
    subscription.save(update_fields=['status', 'updated_at'])


STRIPE_WEBHOOK_HANDLERS = {
    'customer.subscription.updated': _handle_subscription_updated,
    'customer.subscription.deleted': _handle_subscription_deleted,
    'invoice.payment_succeeded': _handle_invoice_payment_succeeded,
    'invoice.payment_failed': _handle_invoice_payment_failed,
}


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    # Stripe isn't a logged-in user: no JWT auth, no DRF parsers (they'd
    # consume request.body before we can verify the signature against it),
    # and CSRF-exempt since this is a server-to-server POST with no session.
    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.SignatureVerificationError):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Read fields from the raw parsed JSON rather than the typed Event
        # object -- stripe-python 15+ typed resources disable dict-style
        # .get() (see SubscriptionStartView above), and we need permissive
        # .get() chains to navigate payload shapes that vary by event type.
        payload_dict = json.loads(payload)
        event_type = payload_dict.get('type')
        obj = (payload_dict.get('data') or {}).get('object') or {}

        # Claim the event via the unique constraint on stripe_event_id
        # *before* running the handler, not after: a check-then-act
        # (exists() then create()) leaves a race window where two
        # redeliveries arriving close together (Stripe retries on timeout or
        # an ambiguous response) can both pass the check and both run the
        # handler. Claiming first means a concurrent duplicate blocks on the
        # same row and then fails with IntegrityError once this transaction
        # commits. If the handler raises, the whole transaction --
        # claim included -- rolls back, so a later retry can still
        # reprocess it from scratch rather than being permanently skipped.
        try:
            with transaction.atomic():
                webhook_event = StripeWebhookEvent.objects.create(
                    stripe_event_id=event.id, type=event_type, payload=payload_dict,
                )
                handler = STRIPE_WEBHOOK_HANDLERS.get(event_type)
                if handler:
                    handler(obj)
                webhook_event.processed_at = dj_timezone.now()
                webhook_event.save(update_fields=['processed_at'])
        except IntegrityError:
            return Response(status=status.HTTP_200_OK)  # already claimed by another delivery

        return Response(status=status.HTTP_200_OK)

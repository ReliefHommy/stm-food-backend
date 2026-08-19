from calendar import monthrange
from datetime import date, datetime, timedelta, timezone

import stripe
from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from thefood.models import Customer, Product

from .models import StripeCustomer, Subscription, SubscriptionItem
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

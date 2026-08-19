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

        box_total = sum(
            products[item['product_id']].price * item['quantity'] for item in requested_items
        )
        box_total_cents = int(box_total * 100)

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

            stripe_subscription = stripe.Subscription.create(
                customer=stripe_customer.stripe_customer_id,
                items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {'name': f'{partner_store.store_name} Subscription Box'},
                            'unit_amount': box_total_cents,
                        },
                        'quantity': 1,
                    },
                    {'price': shipping_price_id, 'quantity': 1},
                ],
                payment_behavior='default_incomplete',
                automatic_tax={'enabled': True},
                expand=['latest_invoice.payment_intent'],
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

        latest_invoice = stripe_subscription.get('latest_invoice')
        payment_intent = latest_invoice.get('payment_intent') if latest_invoice else None
        client_secret = payment_intent.get('client_secret') if payment_intent else None

        box_item, shipping_item = stripe_subscription['items']['data'][0], stripe_subscription['items']['data'][1]

        current_period_end = None
        period_end_ts = stripe_subscription.get('current_period_end')
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
            },
            status=status.HTTP_201_CREATED,
        )

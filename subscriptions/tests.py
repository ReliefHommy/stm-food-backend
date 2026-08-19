from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.test import APIClient

from thefood.models import Customer, PartnerStore, Product, User

from .models import StripeCustomer, Subscription


class FakeStripeObject(dict):
    """Minimal stand-in for a Stripe response object (dict + attribute access)."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


def fake_subscription_response(sub_id='sub_test123'):
    return FakeStripeObject({
        'id': sub_id,
        'items': {
            'data': [
                {'id': 'si_box_test'},
                {'id': 'si_shipping_test'},
            ]
        },
        'latest_invoice': {
            'payment_intent': {'client_secret': 'pi_test_secret_abc'}
        },
        'current_period_end': None,
    })


class SubscriptionStartViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='shopper@example.com', password='testpass123')
        Customer.objects.create(
            user=self.user,
            full_name='Jane Shopper',
            phone='555-1234',
            shipping_address='123 Main St',
            city='Austin',
            postal_code='73301',
            country='US',
        )

        vendor_user = User.objects.create_user(email='vendor@example.com', password='testpass123')
        self.store = PartnerStore.objects.create(
            user=vendor_user, store_name='Thai Flavours', slug='thai-flavours', contact_email='vendor@example.com'
        )
        other_vendor_user = User.objects.create_user(email='vendor2@example.com', password='testpass123')
        self.other_store = PartnerStore.objects.create(
            user=other_vendor_user, store_name='Other Store', slug='other-store', contact_email='vendor2@example.com'
        )

        self.product_a = Product.objects.create(
            title='Pad Thai Kit', description='desc', price=Decimal('12.50'),
            partner_store=self.store, is_subscription_eligible=True,
        )
        self.product_b = Product.objects.create(
            title='Green Curry Kit', description='desc', price=Decimal('15.00'),
            partner_store=self.store, is_subscription_eligible=True,
        )
        self.ineligible_product = Product.objects.create(
            title='One-off Sampler', description='desc', price=Decimal('5.00'),
            partner_store=self.store, is_subscription_eligible=False,
        )
        self.other_store_product = Product.objects.create(
            title='Other Store Item', description='desc', price=Decimal('9.00'),
            partner_store=self.other_store, is_subscription_eligible=True,
        )

        self.client.force_authenticate(user=self.user)

    @patch('subscriptions.views.stripe.Subscription.create')
    @patch('subscriptions.views.stripe.Customer.create')
    def test_happy_path_weekly_creates_django_subscription(self, mock_customer_create, mock_subscription_create):
        mock_customer_create.return_value = MagicMock(id='cus_test123')
        mock_subscription_create.return_value = fake_subscription_response('sub_weekly_1')

        response = self.client.post('/api/subscriptions/start/', {
            'frequency': 'weekly',
            'items': [
                {'product_id': self.product_a.id, 'quantity': 2},
                {'product_id': self.product_b.id, 'quantity': 1},
            ],
        }, format='json')

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['client_secret'], 'pi_test_secret_abc')

        sub = Subscription.objects.get(stripe_subscription_id='sub_weekly_1')
        self.assertEqual(sub.status, 'incomplete')
        self.assertEqual(sub.frequency, 'weekly')
        self.assertEqual(sub.items.count(), 2)
        self.assertEqual(StripeCustomer.objects.get(user=self.user).stripe_customer_id, 'cus_test123')

        # box total = 2*12.50 + 1*15.00 = 40.00 -> 4000 cents
        _, kwargs = mock_subscription_create.call_args
        self.assertEqual(kwargs['items'][0]['price_data']['unit_amount'], 4000)
        self.assertEqual(kwargs['items'][1]['price'], 'price_weekly_dummy')
        self.assertEqual(kwargs['payment_behavior'], 'default_incomplete')
        self.assertTrue(kwargs['automatic_tax']['enabled'])

    @patch('subscriptions.views.stripe.Subscription.create')
    @patch('subscriptions.views.stripe.Customer.modify')
    def test_reuses_existing_stripe_customer_and_picks_biweekly_price(
        self, mock_customer_modify, mock_subscription_create
    ):
        StripeCustomer.objects.create(user=self.user, stripe_customer_id='cus_existing')
        mock_subscription_create.return_value = fake_subscription_response('sub_biweekly_1')

        response = self.client.post('/api/subscriptions/start/', {
            'frequency': 'biweekly',
            'items': [{'product_id': self.product_a.id, 'quantity': 1}],
        }, format='json')

        self.assertEqual(response.status_code, 201, response.data)
        mock_customer_modify.assert_called_once()
        self.assertEqual(StripeCustomer.objects.count(), 1)

        _, kwargs = mock_subscription_create.call_args
        self.assertEqual(kwargs['customer'], 'cus_existing')
        self.assertEqual(kwargs['items'][1]['price'], 'price_biweekly_dummy')

    def test_rejects_mixed_partner_stores(self):
        response = self.client.post('/api/subscriptions/start/', {
            'frequency': 'monthly',
            'items': [
                {'product_id': self.product_a.id, 'quantity': 1},
                {'product_id': self.other_store_product.id, 'quantity': 1},
            ],
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('single partner store', response.data['detail'])
        self.assertFalse(Subscription.objects.exists())

    def test_rejects_ineligible_product(self):
        response = self.client.post('/api/subscriptions/start/', {
            'frequency': 'monthly',
            'items': [{'product_id': self.ineligible_product.id, 'quantity': 1}],
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('not eligible', response.data['detail'])

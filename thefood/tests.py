from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Category, PartnerStore, StoreLocation, Product


class CategoryAPITests(APITestCase):
    def setUp(self):
        Category.objects.create(name='Thai', slug='thai', icon='utensils', image='https://example.com/thai.jpg')
        Category.objects.create(name='Desserts', slug='desserts', icon='cake', image='https://example.com/desserts.jpg')

    def test_list_categories(self):
        url = reverse('category-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Expect two categories
        self.assertEqual(len(resp.data), 2)
        # Ensure expected fields present
        for item in resp.data:
            self.assertIn('id', item)
            self.assertIn('name', item)
            self.assertIn('slug', item)
            self.assertIn('icon', item)
            self.assertIn('image', item)

    def test_retrieve_category_by_slug(self):
        url = reverse('category-detail', kwargs={'slug': 'thai'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['slug'], 'thai')
        self.assertEqual(resp.data['name'], 'Thai')

    def test_retrieve_nonexistent_slug_returns_404(self):
        url = reverse('category-detail', kwargs={'slug': 'nope'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class StoreLocationTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email='vendor@example.com', password='p@ssword', username='vendor')
        self.store = PartnerStore.objects.create(user=self.user, store_name='Vendor 1', contact_email='vendor@example.com')
        self.location = StoreLocation.objects.create(partner_store=self.store, address='123 Market St', city='Bangkok', postal_code='10100', country='Thailand', latitude=13.7563, longitude=100.5018)

    def test_list_store_locations(self):
        url = reverse('storelocation-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        data = resp.data[0]
        self.assertIn('partner_store', data)
        self.assertIn('address', data)
        self.assertEqual(data['address'], '123 Market St')

    def test_retrieve_storelocation(self):
        url = reverse('storelocation-detail', kwargs={'pk': self.location.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['partner_store'], self.store.pk)

    def test_product_auto_assigns_store_location(self):
        # Create product without store_location but with partner_store reference
        product = Product.objects.create(title='Sample', description='desc', price='9.99', partner_store=self.store)
        # After save(), product.store_location should be assigned automatically
        product.refresh_from_db()
        self.assertIsNotNone(product.store_location)
        self.assertEqual(product.store_location.pk, self.location.pk)

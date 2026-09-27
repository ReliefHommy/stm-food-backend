from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Category, PartnerStore, StoreLocation, Product, Recipe, Ingredient


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


class RecipeAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email='chef@example.com', password='p@ssword', username='chef')
        self.store = PartnerStore.objects.create(user=self.user, store_name='Chef Store', slug='chef-store', contact_email='chef@example.com')

        self.other_user = User.objects.create_user(email='other@example.com', password='p@ssword', username='other')
        self.other_store = PartnerStore.objects.create(user=self.other_user, store_name='Other Store', slug='other-store', contact_email='other@example.com')

        self.ingredient = Ingredient.objects.create(name_sv='Lime', slug='lime')
        self.other_ingredient = Ingredient.objects.create(name_sv='Fisksås', slug='fisksas')

        self.available_product = Product.objects.create(
            title='Fresh Lime', description='desc', price='10.00', partner_store=self.store,
            ingredient=self.ingredient, is_available=True,
        )
        self.unavailable_product = Product.objects.create(
            title='Out of Stock Lime', description='desc', price='12.00', partner_store=self.store,
            ingredient=self.ingredient, is_available=False,
        )

        self.recipe = Recipe.objects.create(
            title='Som Tam', slug='som-tam', description='desc',
            ingredients='lime, fish sauce', instructions='mix it all',
            author=self.store,
        )
        self.recipe.ingredient_items.set([self.ingredient])

        self.other_recipe = Recipe.objects.create(
            title='Other Dish', slug='other-dish', description='desc',
            ingredients='n/a', instructions='n/a',
            author=self.other_store,
        )

    def test_list_recipes(self):
        url = reverse('recipe-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)

    def test_filter_recipes_by_store(self):
        url = reverse('recipe-list')
        resp = self.client.get(url, {'store': self.store.slug})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['slug'], 'som-tam')

    def test_retrieve_recipe_by_slug(self):
        url = reverse('recipe-detail', kwargs={'slug': 'som-tam'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['title'], 'Som Tam')
        self.assertEqual(len(resp.data['ingredient_items']), 1)
        self.assertEqual(resp.data['ingredient_items'][0]['slug'], 'lime')

    def test_where_to_buy_only_lists_available_products_for_recipe_ingredients(self):
        url = reverse('recipe-where-to-buy', kwargs={'slug': 'som-tam'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        entry = resp.data[0]
        self.assertEqual(entry['ingredient']['slug'], 'lime')
        self.assertEqual(len(entry['products']), 1)
        self.assertEqual(entry['products'][0]['title'], 'Fresh Lime')

    def test_where_to_buy_empty_for_recipe_without_ingredient_items(self):
        url = reverse('recipe-where-to-buy', kwargs={'slug': 'other-dish'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from .models import Category


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

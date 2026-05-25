from decimal import Decimal

from django.test import TestCase

from .models import Category, Product


class SearchAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        tableware = Category.objects.create(name='Tableware', slug='tableware')
        vase = Category.objects.create(name='Vase', slug='vase')

        Product.objects.create(
            name='Artisan Bowl',
            slug='artisan-bowl',
            description='Textured serving bowl',
            price=Decimal('3200.00'),
            stock=10,
            category=tableware,
            is_available=True,
        )
        Product.objects.create(
            name='Earth Vessel',
            slug='earth-vessel',
            description='Statement vase',
            price=Decimal('8900.00'),
            stock=5,
            category=vase,
            is_available=True,
            is_new=True,
        )
        Product.objects.create(
            name='Hidden Item',
            slug='hidden-item',
            description='Unavailable bowl',
            price=Decimal('100.00'),
            stock=1,
            category=tableware,
            is_available=False,
        )

    def test_search_by_name(self):
        response = self.client.get('/api/search/?q=bowl')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['query'], 'bowl')
        self.assertEqual(body['count'], 1)
        self.assertEqual(body['results'][0]['name'], 'Artisan Bowl')

    def test_search_by_category(self):
        response = self.client.get('/api/search/?q=vase')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)

    def test_search_requires_query(self):
        response = self.client.get('/api/search/')
        self.assertEqual(response.status_code, 400)

    def test_search_min_length(self):
        response = self.client.get('/api/search/?q=a')
        self.assertEqual(response.status_code, 400)

    def test_search_excludes_unavailable(self):
        response = self.client.get('/api/search/?q=hidden')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 0)

    def test_search_with_category_filter(self):
        response = self.client.get('/api/search/?q=bowl&category=Tableware')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)

    def test_products_list_search_alias(self):
        response = self.client.get('/api/products/?search=earth')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

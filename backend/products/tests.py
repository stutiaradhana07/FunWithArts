from decimal import Decimal
from django.test import TestCase
from products.models import Product


class ProductAPITests(TestCase):
    def setUp(self):
        self.p1 = Product.objects.create(
            name='The Guardians',
            description='Handmade decor',
            price=Decimal('7800.00'),
            stock=10,
            category='Decor',
            is_available=True,
            is_new=True,
        )
        self.p2 = Product.objects.create(
            name='Artisan Bowl',
            description='Textured bowl',
            price=Decimal('3200.00'),
            stock=5,
            category='Tableware',
            is_available=True,
            is_new=False,
        )

    def test_product_list(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_product_detail(self):
        response = self.client.get(f'/api/products/{self.p1.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], self.p1.id)
        self.assertEqual(response.json()['isNew'], True)

    def test_product_filter_by_category(self):
        response = self.client.get('/api/products/?category=Decor')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'The Guardians')

    def test_product_filter_category_case_insensitive(self):
        response = self.client.get('/api/products/?category=tableware')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_product_search(self):
        response = self.client.get('/api/products/?search=bowl')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Artisan Bowl')

    def test_product_filter_is_new(self):
        response = self.client.get('/api/products/?is_new=true')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'The Guardians')

    def test_category_list(self):
        response = self.client.get('/api/products/categories/')
        self.assertEqual(response.status_code, 200)
        categories = response.json()
        self.assertIn('Decor', categories)
        self.assertIn('Tableware', categories)
        self.assertEqual(len(categories), 2)

    def test_product_detail_404(self):
        response = self.client.get('/api/products/99999/')
        self.assertEqual(response.status_code, 404)

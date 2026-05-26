from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from products.models import Product, Category


class UserProfileAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='t@t.com', password='pass1234')
        self.token = Token.objects.create(user=self.user)
        self.auth = {'HTTP_AUTHORIZATION': f'Token {self.token.key}'}
        category, _ = Category.objects.get_or_create(name='Tableware')
        self.product = Product.objects.create(
            name='Clay Mug',
            description='A handmade mug',
            price=Decimal('1500.00'),
            stock=5,
            category=category,
            is_available=True,
        )

    def test_profile_get_creates_profile(self):
        response = self.client.get('/api/users/profile/', **self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['city'], '')

    def test_profile_update(self):
        response = self.client.patch(
            '/api/users/profile/',
            {'city': 'Delhi', 'pincode': '110001'},
            content_type='application/json',
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['city'], 'Delhi')

    def test_profile_requires_auth(self):
        response = self.client.get('/api/users/profile/')
        self.assertEqual(response.status_code, 401)

    def test_wishlist_add_and_list(self):
        add = self.client.post(
            '/api/users/wishlist/',
            {'product_id': self.product.id},
            content_type='application/json',
            **self.auth,
        )
        self.assertEqual(add.status_code, 201)

        lst = self.client.get('/api/users/wishlist/', **self.auth)
        self.assertEqual(lst.status_code, 200)
        self.assertEqual(len(lst.json()), 1)
        self.assertEqual(lst.json()[0]['product']['name'], 'Clay Mug')

    def test_wishlist_add_duplicate_returns_200(self):
        self.client.post('/api/users/wishlist/', {'product_id': self.product.id},
                         content_type='application/json', **self.auth)
        dup = self.client.post('/api/users/wishlist/', {'product_id': self.product.id},
                               content_type='application/json', **self.auth)
        self.assertEqual(dup.status_code, 200)
        self.assertEqual(dup.json()['message'], 'Already in wishlist.')

    def test_wishlist_remove(self):
        self.client.post('/api/users/wishlist/', {'product_id': self.product.id},
                         content_type='application/json', **self.auth)
        remove = self.client.delete(
            f'/api/users/wishlist/{self.product.id}/', **self.auth
        )
        self.assertEqual(remove.status_code, 204)
        lst = self.client.get('/api/users/wishlist/', **self.auth)
        self.assertEqual(len(lst.json()), 0)

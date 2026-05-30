from decimal import Decimal
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from rest_framework.authtoken.models import Token
from products.models import Product, Category


class OrderAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_shipping_zones')

    def setUp(self):
        category, _ = Category.objects.get_or_create(name='Vase')
        self.product = Product.objects.create(
            name='Earth Vessel',
            description='Statement vase',
            price=Decimal('8900.00'),
            stock=3,
            category=category,
            is_available=True,
        )
        self.user = User.objects.create_user(username='buyer', email='b@b.com', password='pass1234')
        self.token = Token.objects.create(user=self.user)
        self.auth = {'HTTP_AUTHORIZATION': f'Token {self.token.key}'}

    def _payload(self, product_id, quantity):
        return {
            'contact_email': 'buyer@example.com',
            'contact_phone': '9999999999',
            'shipping_first_name': 'Aarav',
            'shipping_last_name': 'Sharma',
            'shipping_address_line_1': '123 Street',
            'shipping_address_line_2': '',
            'shipping_city': 'Delhi',
            'shipping_state': 'Delhi',
            'shipping_pincode': '110001',
            'payment_method': 'card',
            'items': [{'product_id': product_id, 'quantity': quantity}],
        }

    def test_create_order_success(self):
        response = self.client.post(
            '/api/orders/',
            self._payload(self.product.id, 1),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body['subtotal'], 8900.0)
        self.assertEqual(body['shipping_fee'], 99.0)
        self.assertEqual(body['total_amount'], 8999.0)

    def test_create_order_attaches_user_when_authenticated(self):
        response = self.client.post(
            '/api/orders/',
            self._payload(self.product.id, 1),
            content_type='application/json',
            **self.auth,
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body['user'], self.user.id)

    def test_create_order_fails_invalid_product(self):
        response = self.client.post(
            '/api/orders/',
            self._payload(99999, 1),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_create_order_fails_stock(self):
        response = self.client.post(
            '/api/orders/',
            self._payload(self.product.id, 10),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_delivery_check_valid_and_invalid(self):
        valid = self.client.get('/api/delivery-check/?pincode=110001')
        self.assertEqual(valid.status_code, 200)
        body = valid.json()
        self.assertTrue(body['is_serviceable'])
        self.assertEqual(body['zone_slug'], 'delhi-ncr')
        self.assertIn('business day', body['estimated_delivery'])

        invalid = self.client.get('/api/delivery-check/?pincode=11')
        self.assertEqual(invalid.status_code, 400)

    def test_order_history_requires_auth(self):
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, 401)

    def test_order_history_returns_user_orders(self):
        # Place an order as this user
        self.client.post(
            '/api/orders/',
            self._payload(self.product.id, 1),
            content_type='application/json',
            **self.auth,
        )
        # Re-stock for second check
        self.product.stock = 3
        self.product.save()

        response = self.client.get('/api/orders/', **self.auth)
        self.assertEqual(response.status_code, 200)
        orders = response.json()['results']
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]['contact_email'], 'buyer@example.com')

    def test_order_detail_authenticated(self):
        create_resp = self.client.post(
            '/api/orders/',
            self._payload(self.product.id, 1),
            content_type='application/json',
            **self.auth,
        )
        order_id = create_resp.json()['id']
        detail_resp = self.client.get(f'/api/orders/{order_id}/', **self.auth)
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.json()['id'], order_id)

    def test_order_detail_forbidden_for_other_user(self):
        # Place order as self.user
        create_resp = self.client.post(
            '/api/orders/',
            self._payload(self.product.id, 1),
            content_type='application/json',
            **self.auth,
        )
        order_id = create_resp.json()['id']
        # Try to access as a different user
        other = User.objects.create_user(username='other', email='o@o.com', password='pass5678')
        other_token = Token.objects.create(user=other)
        resp = self.client.get(
            f'/api/orders/{order_id}/',
            HTTP_AUTHORIZATION=f'Token {other_token.key}',
        )
        self.assertEqual(resp.status_code, 404)

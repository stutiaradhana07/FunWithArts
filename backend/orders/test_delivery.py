from decimal import Decimal
from django.test import TestCase
from django.core.management import call_command
from products.models import Product, Category
from .delivery import lookup_pincode


class DeliveryLookupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_shipping_zones')

    def test_delhi_ncr_pincode(self):
        result = lookup_pincode('110001')
        self.assertTrue(result.is_serviceable)
        self.assertEqual(result.zone_slug, 'delhi-ncr')
        self.assertEqual(result.min_delivery_days, 2)
        self.assertIn('2-4', result.estimated_delivery)

    def test_metro_pincode(self):
        result = lookup_pincode('411001')
        self.assertTrue(result.is_serviceable)
        self.assertEqual(result.zone_slug, 'metro')

    def test_region_fallback(self):
        result = lookup_pincode('141001')
        self.assertTrue(result.is_serviceable)
        self.assertEqual(result.zone_slug, 'north-india')

    def test_andaman_not_serviceable(self):
        result = lookup_pincode('744101')
        self.assertFalse(result.is_serviceable)
        self.assertEqual(result.zone_slug, 'remote-islands')

    def test_restricted_ne_prefix(self):
        result = lookup_pincode('790001')
        self.assertFalse(result.is_serviceable)


class DeliveryAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_shipping_zones')
        category, _ = Category.objects.get_or_create(name='Decor')
        cls.product = Product.objects.create(
            name='Test Pot',
            description='Test',
            price=Decimal('1000.00'),
            stock=5,
            category=category,
            is_available=True,
        )

    def test_delivery_check_delhi(self):
        response = self.client.get('/api/delivery-check/?pincode=110001')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['is_serviceable'])
        self.assertEqual(body['zone_slug'], 'delhi-ncr')

    def test_delivery_check_remote(self):
        response = self.client.get('/api/delivery-check/?pincode=744101')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['is_serviceable'])

    def test_delivery_check_invalid(self):
        response = self.client.get('/api/delivery-check/?pincode=11')
        self.assertEqual(response.status_code, 400)

    def test_order_rejects_non_serviceable_pincode(self):
        payload = {
            'contact_email': 'test@example.com',
            'contact_phone': '9999999999',
            'shipping_first_name': 'Test',
            'shipping_last_name': 'User',
            'shipping_address_line_1': '123 Street',
            'shipping_address_line_2': '',
            'shipping_city': 'Port Blair',
            'shipping_state': 'Andaman',
            'shipping_pincode': '744101',
            'payment_method': 'cod',
            'items': [{'product_id': self.product.id, 'quantity': 1}],
        }
        response = self.client.post('/api/orders/', payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

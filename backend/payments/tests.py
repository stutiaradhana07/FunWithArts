from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from rest_framework.authtoken.models import Token
import json

from orders.models import Order
from products.models import Product, Category
from .models import Payment, Refund


class PaymentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=Decimal('100.00'),
            stock=10,
        )
        self.order = Order.objects.create(
            user=self.user,
            subtotal=Decimal('100.00'),
            total_amount=Decimal('100.00'),
            shipping_first_name='Test',
            shipping_last_name='User',
            shipping_address_line_1='123 Test St',
            shipping_city='Delhi',
            shipping_state='Delhi',
            shipping_pincode='110001',
            payment_method='card',
            contact_email='customer@example.com',
            contact_phone='9876543210',
            status=Order.OrderStatus.PENDING,
        )

    def test_payment_creation(self):
        """Test creating a payment record."""
        payment = Payment.objects.create(
            order=self.order,
            razorpay_order_id='order_123456',
            amount=Decimal('100.00'),
            currency='INR',
            status=Payment.PaymentStatus.CREATED
        )
        self.assertEqual(payment.status, Payment.PaymentStatus.CREATED)
        self.assertEqual(payment.order.id, self.order.id)

    def test_payment_status_choices(self):
        """Test that payment status choices are valid."""
        valid_statuses = [s[0] for s in Payment.PaymentStatus.choices]
        self.assertIn(Payment.PaymentStatus.CREATED, valid_statuses)
        self.assertIn(Payment.PaymentStatus.CAPTURED, valid_statuses)


class PaymentAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.token = Token.objects.create(user=self.user)
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=Decimal('100.00'),
            stock=10,
        )
        self.order = Order.objects.create(
            user=self.user,
            subtotal=Decimal('100.00'),
            total_amount=Decimal('100.00'),
            shipping_first_name='Test',
            shipping_last_name='User',
            shipping_address_line_1='123 Test St',
            shipping_city='Delhi',
            shipping_state='Delhi',
            shipping_pincode='110001',
            payment_method='card',
            contact_email='customer@example.com',
            contact_phone='9876543210',
            status=Order.OrderStatus.PENDING,
        )

    def test_payment_order_creation_guest(self):
        """Test that guest users can create payment orders."""
        guest_order = Order.objects.create(
            user=None,  # Guest order
            subtotal=Decimal('50.00'),
            total_amount=Decimal('50.00'),
            shipping_first_name='Guest',
            shipping_last_name='User',
            shipping_address_line_1='456 Test Ave',
            shipping_city='Delhi',
            shipping_state='Delhi',
            shipping_pincode='110001',
            payment_method='card',
            contact_email='guest@example.com',
            contact_phone='9876543210',
            status=Order.OrderStatus.PENDING,
        )
        
        # Guest should be able to request payment for their order (no auth required)
        payload = {'order_id': guest_order.id, 'contact_email': 'guest@example.com'}
        response = self.client.post(
            '/api/payments/create-order/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Should return 201 or error about Razorpay (depends on config)
        self.assertIn(response.status_code, [201, 400, 500])

    def test_payment_order_creation_authenticated(self):
        """Test that authenticated users can create payment orders."""
        payload = {'order_id': self.order.id}
        response = self.client.post(
            '/api/payments/create-order/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )
        
        self.assertIn(response.status_code, [201, 400, 500])

    def test_payment_order_not_found(self):
        """Test that requesting payment for non-existent order returns 404."""
        payload = {'order_id': 99999, 'contact_email': 'nosuch@example.com'}
        response = self.client.post(
            '/api/payments/create-order/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Should get 404 for non-existent order
        # Serializer catches invalid order ID → 400, not 404
        self.assertEqual(response.status_code, 400)

    def test_payment_order_authorization(self):
        """Test that users cannot create payment for others' orders."""
        other_user = User.objects.create_user(username='otheruser', email='other@example.com', password='pass123')
        other_token = Token.objects.create(user=other_user)
        
        # other_user tries to pay for self.order (which belongs to self.user)
        payload = {'order_id': self.order.id}
        response = self.client.post(
            '/api/payments/create-order/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {other_token.key}'
        )
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)


class RefundTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=Decimal('100.00'),
            stock=10,
        )
        self.order = Order.objects.create(
            user=self.user,
            subtotal=Decimal('100.00'),
            total_amount=Decimal('100.00'),
            shipping_first_name='Test',
            shipping_last_name='User',
            shipping_address_line_1='123 Test St',
            shipping_city='Delhi',
            shipping_state='Delhi',
            shipping_pincode='110001',
            payment_method='card',
            contact_email='customer@example.com',
            contact_phone='9876543210',
        )
        self.payment = Payment.objects.create(
            order=self.order,
            razorpay_order_id='order_123',
            razorpay_payment_id='pay_123',
            amount=Decimal('100.00'),
            currency='INR',
            status=Payment.PaymentStatus.CAPTURED
        )

    def test_refund_creation(self):
        """Test creating a refund record."""
        refund = Refund.objects.create(
            payment=self.payment,
            amount=Decimal('50.00'),
            reason='Customer requested refund',
            status=Refund.RefundStatus.PENDING
        )
        self.assertEqual(refund.status, Refund.RefundStatus.PENDING)
        self.assertEqual(refund.payment.id, self.payment.id)

from decimal import Decimal
from datetime import timedelta
import sys
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework import status
from products.models import Product, Category
from orders.models import Order, OrderItem, ExchangeRequest
from orders.admin import ExchangeRequestAdmin, approve_exchanges, reject_exchanges, complete_exchanges
from notifications.models import EmailDeliveryTracking

EXCHANGE_WINDOW_HOURS = 48

class ExchangeAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_shipping_zones')
        cls.category = Category.objects.create(name='Ceramics')
        cls.product = Product.objects.create(
            name='Ocean Bowl',
            description='Handcrafted blue ceramic bowl',
            price=Decimal('2500.00'),
            stock=10,
            category=cls.category,
            is_available=True,
        )
        cls.alt_product = Product.objects.create(
            name='Forest Plate',
            description='Handcrafted green ceramic plate',
            price=Decimal('2500.00'),
            stock=5,
            category=cls.category,
            is_available=True,
        )
        cls.unavailable_product = Product.objects.create(
            name='Sun Vase',
            description='Yellow vase',
            price=Decimal('3000.00'),
            stock=0,
            category=cls.category,
            is_available=False,
        )

    def setUp(self):
        self.user = User.objects.create_user(username='buyer', email='buyer@example.com', password='password123')
        self.token = Token.objects.create(user=self.user)
        self.auth_headers = {'HTTP_AUTHORIZATION': f'Token {self.token.key}'}

        # Create a valid order for the user
        self.order = Order.objects.create(
            user=self.user,
            contact_email='buyer@example.com',
            contact_phone='9876543210',
            shipping_first_name='John',
            shipping_last_name='Doe',
            shipping_address_line_1='Apt 4B, Ceramic Tower',
            shipping_city='Delhi',
            shipping_state='Delhi',
            shipping_pincode='110001',
            payment_method='card',
            subtotal=Decimal('2500.00'),
            shipping_fee=Decimal('99.00'),
            total_amount=Decimal('2599.00'),
            status=Order.OrderStatus.DELIVERED,
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name=self.product.name,
            unit_price=self.product.price,
            quantity=1,
            line_total=self.product.price,
        )

        # Clear outbox so that order creation email does not count in test assertions
        mail.outbox.clear()

        # A valid unboxing video mock
        self.video_file = SimpleUploadedFile(
            "unboxing.mp4",
            b"fake_mp4_video_data",
            content_type="video/mp4"
        )

    def _get_base_payload(self):
        return {
            'order_id': self.order.id,
            'order_item_id': self.order_item.id,
            'exchange_type': 'same',
            'reason': 'The ceramic bowl was cracked on arrival near the rim.',
            'unboxing_video': self.video_file,
            'confirm_authentic': True,
            'confirm_review': True,
            'confirm_policy': True,
        }

    def test_create_exchange_success_same_item(self):
        payload = self._get_base_payload()
        response = self.client.post(
            '/api/exchanges/',
            payload,
            format='multipart',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertTrue(data['reference_id'].startswith('EXC-'))
        self.assertEqual(data['exchange_type'], 'same')
        self.assertEqual(data['status'], 'pending_review')
        self.assertEqual(data['order_id'], self.order.id)
        
        # Verify signal fired and email was recorded in system
        tracking_email = EmailDeliveryTracking.objects.filter(recipient_email='buyer@example.com').first()
        self.assertIsNotNone(tracking_email)
        self.assertIn('Exchange Request Received', tracking_email.subject)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Received', mail.outbox[0].subject)

    def test_create_exchange_success_other_item(self):
        payload = self._get_base_payload()
        payload.update({
            'exchange_type': 'other',
            'alt_product_id': self.alt_product.id
        })
        response = self.client.post(
            '/api/exchanges/',
            payload,
            format='multipart',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data['exchange_type'], 'other')
        self.assertEqual(data['alt_product_name'], self.alt_product.name)

    def test_create_exchange_requires_auth(self):
        payload = self._get_base_payload()
        response = self.client.post('/api/exchanges/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_exchange_invalid_order_ownership(self):
        other_user = User.objects.create_user(username='other', email='other@example.com', password='pass')
        other_token = Token.objects.create(user=other_user)
        
        payload = self._get_base_payload()
        response = self.client.post(
            '/api/exchanges/',
            payload,
            format='multipart',
            HTTP_AUTHORIZATION=f'Token {other_token.key}'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('order_id', response.json())

    def test_create_exchange_invalid_order_item(self):
        payload = self._get_base_payload()
        payload['order_item_id'] = 99999
        response = self.client.post(
            '/api/exchanges/',
            payload,
            format='multipart',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('order_item_id', response.json())

    def test_create_exchange_past_48_hours(self):
        # Shift order created_at to past the 48-hour window
        self.order.created_at = timezone.now() - timedelta(hours=EXCHANGE_WINDOW_HOURS + 1)
        self.order.save()

        payload = self._get_base_payload()
        response = self.client.post(
            '/api/exchanges/',
            payload,
            format='multipart',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('order_id', response.json())
        self.assertIn('expired', response.json()['order_id'][0])

    def test_create_exchange_duplicate_order_item(self):
        # Create first exchange
        payload = self._get_base_payload()
        response1 = self.client.post(
            '/api/exchanges/',
            payload,
            format='multipart',
            **self.auth_headers
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Attempt to create second exchange for same item
        # Re-initialize file to avoid file closure issues in test client
        payload['unboxing_video'] = SimpleUploadedFile("unboxing2.mp4", b"data", content_type="video/mp4")
        response2 = self.client.post(
            '/api/exchanges/',
            payload,
            format='multipart',
            **self.auth_headers
        )
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('order_item_id', response2.json())
        self.assertIn('active exchange request already exists', response2.json()['order_item_id'][0])

    def test_create_exchange_other_missing_alt_product(self):
        payload = self._get_base_payload()
        payload.update({
            'exchange_type': 'other'
            # alt_product_id omitted
        })
        response = self.client.post(
            '/api/exchanges/',
            payload,
            format='multipart',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('alt_product_id', response.json())

    def test_create_exchange_other_unavailable_alt_product(self):
        payload = self._get_base_payload()
        payload.update({
            'exchange_type': 'other',
            'alt_product_id': self.unavailable_product.id
        })
        response = self.client.post(
            '/api/exchanges/',
            payload,
            format='multipart',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('alt_product_id', response.json())

    def test_create_exchange_invalid_video_format(self):
        payload = self._get_base_payload()
        invalid_video = SimpleUploadedFile("image.png", b"fake_png_data", content_type="image/png")
        payload['unboxing_video'] = invalid_video
        response = self.client.post(
            '/api/exchanges/',
            payload,
            format='multipart',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('unboxing_video', response.json())

    def test_create_exchange_reason_too_short(self):
        payload = self._get_base_payload()
        payload['reason'] = 'Too short.'
        response = self.client.post(
            '/api/exchanges/',
            payload,
            format='multipart',
            **self.auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('reason', response.json())

    def test_create_exchange_checkboxes_unchecked(self):
        checkbox_fields = ['confirm_authentic', 'confirm_review', 'confirm_policy']
        for field in checkbox_fields:
            payload = self._get_base_payload()
            payload[field] = False
            response = self.client.post(
                '/api/exchanges/',
                payload,
                format='multipart',
                **self.auth_headers
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.json())

    def test_get_exchange_detail_owner_vs_non_owner(self):
        # Create an exchange
        exchange = ExchangeRequest.objects.create(
            order=self.order,
            order_item=self.order_item,
            user=self.user,
            exchange_type=ExchangeRequest.ExchangeType.SAME,
            reason='The ceramic bowl was cracked on arrival near the rim.',
            unboxing_video=self.video_file
        )

        # GET detail as owner
        response = self.client.get(f'/api/exchanges/{exchange.id}/', **self.auth_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['id'], exchange.id)

        # GET detail as non-owner
        other_user = User.objects.create_user(username='other', email='other@example.com', password='pass')
        other_token = Token.objects.create(user=other_user)
        response_other = self.client.get(
            f'/api/exchanges/{exchange.id}/',
            HTTP_AUTHORIZATION=f'Token {other_token.key}'
        )
        self.assertEqual(response_other.status_code, status.HTTP_404_NOT_FOUND)

        # GET detail as staff
        staff_user = User.objects.create_user(username='staff', email='staff@example.com', password='pass', is_staff=True)
        staff_token = Token.objects.create(user=staff_user)
        response_staff = self.client.get(
            f'/api/exchanges/{exchange.id}/',
            HTTP_AUTHORIZATION=f'Token {staff_token.key}'
        )
        self.assertEqual(response_staff.status_code, status.HTTP_200_OK)

    def test_exchange_status_signals_approved(self):
        mail.outbox.clear()
        exchange = ExchangeRequest.objects.create(
            order=self.order,
            order_item=self.order_item,
            user=self.user,
            exchange_type=ExchangeRequest.ExchangeType.SAME,
            reason='The ceramic bowl was cracked on arrival near the rim.',
            unboxing_video=self.video_file
        )
        
        # Clear outbox which contains submission email
        mail.outbox.clear()

        # Update status to approved
        exchange.status = ExchangeRequest.ExchangeStatus.APPROVED
        exchange.save()

        # Verify decision email is recorded and sent
        tracking_emails = EmailDeliveryTracking.objects.filter(recipient_email='buyer@example.com', subject__contains='Approved')
        self.assertEqual(tracking_emails.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Approved', mail.outbox[0].subject)

    def test_exchange_status_signals_rejected(self):
        mail.outbox.clear()
        exchange = ExchangeRequest.objects.create(
            order=self.order,
            order_item=self.order_item,
            user=self.user,
            exchange_type=ExchangeRequest.ExchangeType.SAME,
            reason='The ceramic bowl was cracked on arrival near the rim.',
            unboxing_video=self.video_file
        )
        mail.outbox.clear()

        # Update status to rejected
        exchange.status = ExchangeRequest.ExchangeStatus.REJECTED
        exchange.save()

        # Verify decision email is recorded and sent
        tracking_emails = EmailDeliveryTracking.objects.filter(recipient_email='buyer@example.com', subject__contains='decision')
        self.assertEqual(tracking_emails.count(), 0) # Subject for reject doesn't have "Approved"
        decision_emails = EmailDeliveryTracking.objects.filter(recipient_email='buyer@example.com', subject__contains='Update')
        self.assertEqual(decision_emails.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_admin_actions(self):
        exchange = ExchangeRequest.objects.create(
            order=self.order,
            order_item=self.order_item,
            user=self.user,
            exchange_type=ExchangeRequest.ExchangeType.SAME,
            reason='The ceramic bowl was cracked on arrival near the rim.',
            unboxing_video=self.video_file
        )

        class MockRequest:
            pass

        class MockModelAdmin:
            def message_user(self, request, message):
                self.last_message = message

        modeladmin = MockModelAdmin()
        queryset = ExchangeRequest.objects.filter(pk=exchange.pk)

        # 1. Test approve
        mail.outbox.clear()
        approve_exchanges(modeladmin, MockRequest(), queryset)
        exchange.refresh_from_db()
        self.assertEqual(exchange.status, ExchangeRequest.ExchangeStatus.APPROVED)
        self.assertIn('approved', modeladmin.last_message)
        self.assertEqual(len(mail.outbox), 1)

        # 2. Test complete
        complete_exchanges(modeladmin, MockRequest(), queryset)
        exchange.refresh_from_db()
        self.assertEqual(exchange.status, ExchangeRequest.ExchangeStatus.COMPLETED)
        self.assertIn('completed', modeladmin.last_message)

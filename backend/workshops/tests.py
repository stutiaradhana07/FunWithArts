from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from rest_framework.authtoken.models import Token
import json

from .models import Workshop, Booking


# ──────────────────────────────────────────────
#  Model Tests
# ──────────────────────────────────────────────

class WorkshopModelTests(TestCase):
    def setUp(self):
        self.workshop = Workshop.objects.create(
            title='Painting 101',
            description='Learn basic painting techniques',
            instructor='John Doe',
            date=date.today() + timedelta(days=7),
            time='10:00',
            duration=120,
            price=Decimal('50.00'),
            total_slots=20,
            available_slots=20,
            is_active=True
        )

    def test_workshop_creation(self):
        """Test workshop is created with correct fields."""
        self.assertEqual(self.workshop.title, 'Painting 101')
        self.assertEqual(self.workshop.available_slots, 20)
        self.assertTrue(self.workshop.is_active)

    def test_workshop_string_representation(self):
        """Test workshop string representation."""
        self.assertEqual(str(self.workshop), 'Painting 101')


class BookingModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='pass123')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='pass123')
        self.workshop = Workshop.objects.create(
            title='Painting 101',
            description='Learn basic painting techniques',
            instructor='John Doe',
            date=date.today() + timedelta(days=7),
            time='10:00',
            duration=120,
            price=Decimal('50.00'),
            total_slots=20,
            available_slots=20,
            is_active=True
        )

    def test_booking_creation_defaults_pending(self):
        """Test booking is created with PENDING payment status by default."""
        booking = Booking.objects.create(
            user=self.user1,
            workshop=self.workshop,
            seats=2
        )
        self.assertEqual(booking.user.username, 'user1')
        self.assertEqual(booking.workshop.title, 'Painting 101')
        self.assertEqual(booking.seats, 2)
        self.assertEqual(booking.payment_status, Booking.PaymentStatus.PENDING)

    def test_multiple_bookings_allowed_for_retries(self):
        """Users can create multiple bookings for the same workshop (retries are allowed)."""
        Booking.objects.create(user=self.user1, workshop=self.workshop, seats=1, payment_status=Booking.PaymentStatus.FAILED)
        # Retry after failed payment — should be allowed (no unique_together)
        booking2 = Booking.objects.create(user=self.user1, workshop=self.workshop, seats=1, payment_status=Booking.PaymentStatus.PENDING)
        self.assertIsNotNone(booking2)
        self.assertEqual(Booking.objects.filter(user=self.user1, workshop=self.workshop).count(), 2)

    def test_different_users_can_book_same_workshop(self):
        """Test that different users can book the same workshop."""
        booking1 = Booking.objects.create(user=self.user1, workshop=self.workshop, seats=1)
        booking2 = Booking.objects.create(user=self.user2, workshop=self.workshop, seats=1)
        self.assertNotEqual(booking1.user, booking2.user)
        self.assertEqual(booking1.workshop, booking2.workshop)

    def test_payment_status_choices(self):
        """Test that PaymentStatus choices are valid."""
        valid_statuses = [s[0] for s in Booking.PaymentStatus.choices]
        self.assertIn('pending', valid_statuses)
        self.assertIn('confirmed', valid_statuses)
        self.assertIn('failed', valid_statuses)
        self.assertIn('cancelled', valid_statuses)


# ──────────────────────────────────────────────
#  API Tests
# ──────────────────────────────────────────────

class WorkshopAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.token = Token.objects.create(user=self.user)

        self.past_workshop = Workshop.objects.create(
            title='Past Workshop',
            description='Old workshop',
            instructor='Jane Doe',
            date=date.today() - timedelta(days=7),
            time='10:00',
            duration=120,
            price=Decimal('50.00'),
            total_slots=20,
            available_slots=20,
            is_active=True
        )

        self.future_workshop = Workshop.objects.create(
            title='Future Workshop',
            description='Upcoming workshop',
            instructor='John Doe',
            date=date.today() + timedelta(days=7),
            time='10:00',
            duration=120,
            price=Decimal('50.00'),
            total_slots=20,
            available_slots=20,
            is_active=True
        )

    def test_list_workshops_excludes_past(self):
        """Test that workshop list excludes past workshops."""
        response = self.client.get('/api/workshops/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        workshop_ids = [w['id'] for w in data]
        self.assertIn(self.future_workshop.id, workshop_ids)
        self.assertNotIn(self.past_workshop.id, workshop_ids)

    def test_workshop_detail(self):
        """Test retrieving a workshop detail."""
        response = self.client.get(f'/api/workshops/{self.future_workshop.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['title'], 'Future Workshop')


class WorkshopPaymentAPITests(TestCase):
    """Tests for the Razorpay-backed workshop booking flow."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.token = Token.objects.create(user=self.user)

        self.workshop = Workshop.objects.create(
            title='Pottery Basics',
            description='Learn pottery',
            instructor='Jane Doe',
            date=date.today() + timedelta(days=14),
            time='14:00',
            duration=180,
            price=Decimal('100.00'),
            total_slots=10,
            available_slots=10,
            is_active=True
        )

    # ── initiate-payment ──

    def test_initiate_payment_requires_auth(self):
        """Initiate payment requires authentication."""
        response = self.client.post(
            '/api/workshops/initiate-payment/',
            data=json.dumps({'workshop_id': self.workshop.id, 'seats': 1}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)

    @patch('workshops.views._get_razorpay_client')
    def test_initiate_payment_creates_booking_and_order(self, mock_client):
        """Initiate payment creates a PENDING booking and a Razorpay order."""
        mock_razorpay = MagicMock()
        mock_razorpay.order.create.return_value = {
            'id': 'order_test123',
            'amount': 20000,
            'currency': 'INR',
            'status': 'created',
        }
        mock_client.return_value = mock_razorpay

        response = self.client.post(
            '/api/workshops/initiate-payment/',
            data=json.dumps({'workshop_id': self.workshop.id, 'seats': 2}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['razorpay_order_id'], 'order_test123')
        self.assertEqual(data['amount'], 20000)  # 100 * 2 seats * 100 paise
        self.assertEqual(data['currency'], 'INR')

        # Booking created with PENDING status
        booking = Booking.objects.filter(user=self.user, workshop=self.workshop).first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.payment_status, Booking.PaymentStatus.PENDING)
        self.assertEqual(booking.seats, 2)
        self.assertEqual(booking.razorpay_order_id, 'order_test123')

        # Slots deducted
        self.workshop.refresh_from_db()
        self.assertEqual(self.workshop.available_slots, 8)

    def test_initiate_payment_past_workshop_rejected(self):
        """Cannot initiate payment for a past workshop."""
        past = Workshop.objects.create(
            title='Past',
            description='Old',
            instructor='X',
            date=date.today() - timedelta(days=1),
            time='10:00',
            duration=60,
            price=Decimal('10.00'),
            total_slots=5,
            available_slots=5,
            is_active=True
        )

        response = self.client.post(
            '/api/workshops/initiate-payment/',
            data=json.dumps({'workshop_id': past.id, 'seats': 1}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )
        self.assertEqual(response.status_code, 400)

    @patch('workshops.views._get_razorpay_client')
    def test_initiate_payment_insufficient_slots(self, mock_client):
        """Cannot initiate payment for more seats than available."""
        self.workshop.available_slots = 1
        self.workshop.save()

        response = self.client.post(
            '/api/workshops/initiate-payment/',
            data=json.dumps({'workshop_id': self.workshop.id, 'seats': 3}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )
        self.assertEqual(response.status_code, 400)

    @patch('workshops.views._get_razorpay_client')
    def test_initiate_payment_duplicate_confirmed_blocked(self, mock_client):
        """Cannot re-book a workshop that already has a CONFIRMED booking."""
        mock_razorpay = MagicMock()
        mock_razorpay.order.create.return_value = {
            'id': 'order_test456',
            'amount': 10000,
            'currency': 'INR',
            'status': 'created',
        }
        mock_client.return_value = mock_razorpay

        # First booking — succeeds
        self.client.post(
            '/api/workshops/initiate-payment/',
            data=json.dumps({'workshop_id': self.workshop.id, 'seats': 1}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )

        # Manually confirm the first booking (simulate payment verification)
        booking = Booking.objects.get(user=self.user, workshop=self.workshop)
        booking.payment_status = Booking.PaymentStatus.CONFIRMED
        booking.save()

        # Second attempt — blocked
        response = self.client.post(
            '/api/workshops/initiate-payment/',
            data=json.dumps({'workshop_id': self.workshop.id, 'seats': 1}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )
        self.assertEqual(response.status_code, 400)

    @patch('workshops.views._get_razorpay_client')
    def test_initiate_payment_allows_retry_after_failed(self, mock_client):
        """Users can retry payment after a previous FAILED booking."""
        # Create a failed booking first
        Booking.objects.create(
            user=self.user,
            workshop=self.workshop,
            seats=1,
            payment_status=Booking.PaymentStatus.FAILED,
        )
        self.workshop.available_slots -= 1  # simulate slot already deducted
        self.workshop.save()

        mock_razorpay = MagicMock()
        mock_razorpay.order.create.return_value = {
            'id': 'order_retry789',
            'amount': 10000,
            'currency': 'INR',
            'status': 'created',
        }
        mock_client.return_value = mock_razorpay

        # Retry — should succeed
        response = self.client.post(
            '/api/workshops/initiate-payment/',
            data=json.dumps({'workshop_id': self.workshop.id, 'seats': 1}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )
        self.assertEqual(response.status_code, 201)

    # ── verify-payment ──

    @patch('workshops.views._get_razorpay_client')
    def test_verify_payment_confirms_booking(self, mock_client):
        """Successful signature verification transitions booking to CONFIRMED."""
        # Create a pending booking with a known razorpay_order_id
        booking = Booking.objects.create(
            user=self.user,
            workshop=self.workshop,
            seats=1,
            payment_status=Booking.PaymentStatus.PENDING,
            razorpay_order_id='order_verify_test',
        )
        self.workshop.available_slots -= 1
        self.workshop.save()

        mock_razorpay = MagicMock()
        # Signature verification succeeds (returns no exception)
        mock_razorpay.utility.verify_payment_signature.return_value = True
        mock_client.return_value = mock_razorpay

        response = self.client.post(
            '/api/workshops/payment/verify/',
            data=json.dumps({
                'razorpay_order_id': 'order_verify_test',
                'razorpay_payment_id': 'pay_test123',
                'razorpay_signature': 'sig_test123',
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )

        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.payment_status, Booking.PaymentStatus.CONFIRMED)
        self.assertEqual(booking.razorpay_payment_id, 'pay_test123')

    def test_verify_payment_requires_auth(self):
        """Verify payment endpoint requires authentication."""
        response = self.client.post(
            '/api/workshops/payment/verify/',
            data=json.dumps({
                'razorpay_order_id': 'order_test',
                'razorpay_payment_id': 'pay_test',
                'razorpay_signature': 'sig_test',
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)

    def test_verify_payment_invalid_order_id(self):
        """Verify with non-existent order_id returns 404."""
        response = self.client.post(
            '/api/workshops/payment/verify/',
            data=json.dumps({
                'razorpay_order_id': 'nonexistent_order',
                'razorpay_payment_id': 'pay_test',
                'razorpay_signature': 'sig_test',
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )
        self.assertEqual(response.status_code, 404)


# ──────────────────────────────────────────────
#  Webhook Tests
# ──────────────────────────────────────────────

class WorkshopWebhookTests(TestCase):
    """Tests for the Razorpay webhook fallback endpoint."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='webhookuser', email='web@example.com', password='pass123')
        self.token = Token.objects.create(user=self.user)

        self.workshop = Workshop.objects.create(
            title='Webhook Workshop',
            description='Testing webhooks',
            instructor='Jane Doe',
            date=date.today() + timedelta(days=14),
            time='14:00',
            duration=180,
            price=Decimal('100.00'),
            total_slots=10,
            available_slots=8,  # 2 seats already deducted for the pending booking below
            is_active=True
        )

        self.webhook_url = '/api/workshops/payment/webhook/'

    def _payload(self, event, order_id, payment_id='pay_webhook_test'):
        """Build a Razorpay webhook JSON payload matching real structure."""
        import json as _json
        return _json.dumps({
            'event': event,
            'payload': {
                'payment': {
                    'entity': {
                        'id': payment_id,
                        'order_id': order_id,
                        'method': 'upi',
                    }
                }
            },
        })

    def _sign(self, payload: bytes) -> str:
        """Generate a valid HMAC-SHA256 signature for the given payload."""
        import hashlib as _hashlib, hmac as _hmac
        from django.conf import settings
        secret = settings.RAZORPAY_WEBHOOK_SECRET
        return _hmac.new(secret.encode(), payload, _hashlib.sha256).hexdigest()

    # ── Signature validation ──

    def test_webhook_missing_signature_returns_400(self):
        """No X-Razorpay-Signature header → 400."""
        response = self.client.post(
            self.webhook_url,
            data=self._payload('payment.captured', 'order_no_sig'),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_webhook_invalid_signature_returns_400(self):
        """Wrong HMAC signature → 400."""
        payload_str = self._payload('payment.captured', 'order_bad_sig')
        response = self.client.post(
            self.webhook_url,
            data=payload_str,
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE='deadbeef' * 8,
        )
        self.assertEqual(response.status_code, 400)

    def test_webhook_invalid_json_returns_400(self):
        """Malformed JSON body → 400."""
        payload = b'not valid json'
        sig = self._sign(payload)
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE=sig,
        )
        self.assertEqual(response.status_code, 400)

    # ── payment.captured ──

    def test_webhook_captured_confirms_booking(self):
        """payment.captured → marks PENDING booking as CONFIRMED."""
        booking = Booking.objects.create(
            user=self.user,
            workshop=self.workshop,
            seats=2,
            payment_status=Booking.PaymentStatus.PENDING,
            razorpay_order_id='order_captured_1',
        )

        payload_str = self._payload('payment.captured', 'order_captured_1', 'pay_abc123')
        sig = self._sign(payload_str.encode())

        response = self.client.post(
            self.webhook_url,
            data=payload_str,
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE=sig,
        )

        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.payment_status, Booking.PaymentStatus.CONFIRMED)
        self.assertEqual(booking.razorpay_payment_id, 'pay_abc123')

    def test_webhook_captured_idempotent_on_confirmed(self):
        """payment.captured for an already CONFIRMED booking is safe (no-op)."""
        booking = Booking.objects.create(
            user=self.user,
            workshop=self.workshop,
            seats=1,
            payment_status=Booking.PaymentStatus.CONFIRMED,
            razorpay_order_id='order_already_confirmed',
            razorpay_payment_id='pay_original',
        )

        payload_str = self._payload('payment.captured', 'order_already_confirmed', 'pay_duplicate')
        sig = self._sign(payload_str.encode())

        response = self.client.post(
            self.webhook_url,
            data=payload_str,
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE=sig,
        )

        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        # Still CONFIRMED with original payment_id (not overwritten)
        self.assertEqual(booking.payment_status, Booking.PaymentStatus.CONFIRMED)
        self.assertEqual(booking.razorpay_payment_id, 'pay_original')

    def test_webhook_captured_unknown_order_returns_200(self):
        """payment.captured for an unknown order_id → graceful 200 (not a workshop order)."""
        payload_str = self._payload('payment.captured', 'order_no_such_booking', 'pay_unknown')
        sig = self._sign(payload_str.encode())

        response = self.client.post(
            self.webhook_url,
            data=payload_str,
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE=sig,
        )

        self.assertEqual(response.status_code, 200)

    # ── payment.failed ──

    def test_webhook_failed_marks_booking_failed_and_releases_slots(self):
        """payment.failed → marks PENDING booking FAILED + releases seats."""
        booking = Booking.objects.create(
            user=self.user,
            workshop=self.workshop,
            seats=2,
            payment_status=Booking.PaymentStatus.PENDING,
            razorpay_order_id='order_failed_1',
        )

        slots_before = self.workshop.available_slots  # 8

        payload_str = self._payload('payment.failed', 'order_failed_1', 'pay_fail123')
        sig = self._sign(payload_str.encode())

        response = self.client.post(
            self.webhook_url,
            data=payload_str,
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE=sig,
        )

        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.workshop.refresh_from_db()

        self.assertEqual(booking.payment_status, Booking.PaymentStatus.FAILED)
        self.assertEqual(self.workshop.available_slots, slots_before + 2)  # seats released

    def test_webhook_failed_ignores_confirmed_booking(self):
        """payment.failed for a CONFIRMED booking → ignored (no status change, no slot release)."""
        booking = Booking.objects.create(
            user=self.user,
            workshop=self.workshop,
            seats=1,
            payment_status=Booking.PaymentStatus.CONFIRMED,
            razorpay_order_id='order_confirmed_fail_hook',
            razorpay_payment_id='pay_confirmed',
        )

        slots_before = self.workshop.available_slots

        payload_str = self._payload('payment.failed', 'order_confirmed_fail_hook', 'pay_confirmed')
        sig = self._sign(payload_str.encode())

        response = self.client.post(
            self.webhook_url,
            data=payload_str,
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE=sig,
        )

        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.workshop.refresh_from_db()

        # Still CONFIRMED, slots unchanged
        self.assertEqual(booking.payment_status, Booking.PaymentStatus.CONFIRMED)
        self.assertEqual(self.workshop.available_slots, slots_before)

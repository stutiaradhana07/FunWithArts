from datetime import date, time
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth.models import User

from orders.models import Order
from workshops.models import Workshop, Booking
from users.models import UserProfile

from notifications.whatsapp import format_phone_number, send_whatsapp_async


class WhatsAppUtilityTests(TestCase):
    """Test WhatsApp formatting and utility functions."""

    def test_format_phone_number_india(self):
        """Standard 10-digit Indian numbers should get prefix +91."""
        self.assertEqual(format_phone_number("9876543210"), "+919876543210")
        self.assertEqual(format_phone_number(" 9876-543 210 "), "+919876543210")

    def test_format_phone_number_already_formatted(self):
        """Numbers starting with + should be left intact."""
        self.assertEqual(format_phone_number("+919876543210"), "+919876543210")
        self.assertEqual(format_phone_number("+14155238886"), "+14155238886")

    @patch('notifications.whatsapp.requests.post')
    @patch('notifications.whatsapp.logger')
    def test_send_whatsapp_console_fallback(self, mock_logger, mock_post):
        """Default 'console' provider should print message without making API requests."""
        send_whatsapp_async(
            recipient_phone="9876543210",
            template_name="order_confirmed",
            variables={"name": "Alice", "order_id": "123", "total_amount": "1450.00"}
        )
        
        # Verify no POST call was made
        mock_post.assert_not_called()
        
        # Verify logger.info was called with sandbox header
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        self.assertTrue(any("WHATSAPP SANDBOX LOG" in log for log in log_calls))

    @patch('notifications.whatsapp.requests.post')
    @patch('django.conf.settings.WHATSAPP_PROVIDER', 'twilio')
    @patch('django.conf.settings.TWILIO_ACCOUNT_SID', 'ACxxxxx')
    @patch('django.conf.settings.TWILIO_AUTH_TOKEN', 'tokenxxxxx')
    @patch('django.conf.settings.TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
    def test_send_whatsapp_twilio_provider(self, mock_post):
        """Twilio provider should trigger basicauth HTTP POST request."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        send_whatsapp_async(
            recipient_phone="9876543210",
            template_name="order_confirmed",
            variables={"name": "Alice", "order_id": "123", "total_amount": "1450.00"}
        )

        mock_post.assert_called_once()
        call_args, call_kwargs = mock_post.call_args
        
        # Verify target URL and headers
        self.assertEqual(call_args[0], "https://api.twilio.com/2010-04-01/Accounts/ACxxxxx/Messages.json")
        self.assertEqual(call_kwargs['auth'], ('ACxxxxx', 'tokenxxxxx'))
        self.assertEqual(call_kwargs['data']['To'], "whatsapp:+919876543210")
        self.assertEqual(call_kwargs['data']['From'], "whatsapp:+14155238886")
        self.assertTrue("Alice" in call_kwargs['data']['Body'])


class WhatsAppSignalTests(TestCase):
    """Test WhatsApp signal triggers on orders and bookings."""

    def setUp(self):
        # Create user and profile
        self.user = User.objects.create_user(username='testuser', email='t@t.com', password='pass1234')
        self.profile = UserProfile.objects.create(user=self.user, phone="9876543210")
        
        # Create workshop
        self.workshop = Workshop.objects.create(
            title="Pottery Experience",
            description="Learn to mold clay",
            instructor="Chef Clay",
            date=date(2026, 6, 15),
            time=time(14, 30),
            duration=120,
            price=Decimal("1200.00"),
            total_slots=10,
            available_slots=10
        )

    @patch('notifications.signals.send_whatsapp_async')
    def test_order_confirmation_signal(self, mock_send_whatsapp):
        """Signal should trigger WhatsApp confirmation only when order status transitions to CONFIRMED."""
        # Create a pending order
        order = Order.objects.create(
            user=self.user,
            contact_email="t@t.com",
            contact_phone="9876543210",
            shipping_first_name="Alice",
            shipping_last_name="Aradhana",
            shipping_address_line_1="123 Studio Way",
            shipping_city="Delhi",
            shipping_state="Delhi",
            shipping_pincode="110001",
            payment_method=Order.PaymentMethod.UPI,
            subtotal=Decimal("1500.00"),
            total_amount=Decimal("1500.00"),
            status=Order.OrderStatus.PENDING
        )
        
        # Should not trigger WhatsApp on creation (status is PENDING)
        mock_send_whatsapp.assert_not_called()

        # Update status to CONFIRMED
        order.status = Order.OrderStatus.CONFIRMED
        order.save()

        # Signal should fire WhatsApp message
        mock_send_whatsapp.assert_called_once_with(
            "9876543210",
            "order_confirmed",
            {
                "name": "Alice",
                "order_id": str(order.id),
                "total_amount": "1500.00"
            }
        )
        
        # Reset mock and save again as CONFIRMED (no transition, no extra message)
        mock_send_whatsapp.reset_mock()
        order.save()
        mock_send_whatsapp.assert_not_called()

    @patch('notifications.signals.send_whatsapp_async')
    def test_workshop_booking_confirmation_signal(self, mock_send_whatsapp):
        """Signal should trigger WhatsApp confirmation when payment_status transitions to CONFIRMED."""
        # Create booking starting in PENDING
        booking = Booking.objects.create(
            user=self.user,
            workshop=self.workshop,
            seats=2,
            payment_status=Booking.PaymentStatus.PENDING
        )

        # Should not fire WhatsApp on pending creation
        mock_send_whatsapp.assert_not_called()

        # Confirm booking payment
        booking.payment_status = Booking.PaymentStatus.CONFIRMED
        booking.save()

        from django.utils import timezone
        local_time = timezone.localtime(booking.updated_at)

        # WhatsApp should fire
        mock_send_whatsapp.assert_called_once_with(
            "9876543210",
            "workshop_booked",
            {
                "name": "testuser",
                "workshop_title": "Pottery Experience",
                "payment_date": local_time.strftime('%d-%b-%Y'),
                "payment_time": local_time.strftime('%I:%M %p')
            }
        )

        # Reset mock and save again as CONFIRMED (no state change, no extra message)
        mock_send_whatsapp.reset_mock()
        booking.save()
        mock_send_whatsapp.assert_not_called()

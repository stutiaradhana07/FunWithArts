"""
Signal handlers that fire transactional emails and WhatsApp texts when key business events occur.

Triggers:
    - order_placed              → order confirmation receipt (email)
    - order_confirmed           → order confirmation alert (WhatsApp)
    - order_shipped             → shipping notification with tracking context (email)
    - workshop_booked           → workshop booking confirmation (email)
    - workshop_confirmed        → workshop booking confirmation (WhatsApp)
"""

import logging
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.template.loader import render_to_string

from orders.models import Order
from workshops.models import Booking

from .emails import send_email_async
from .whatsapp import send_whatsapp_async

logger = logging.getLogger('notifications')


# ──────────────────────────────────────────────────────────────────────
# Status Transition Trackers
# ──────────────────────────────────────────────────────────────────────

@receiver(pre_save, sender=Order)
def on_order_pre_save(sender, instance, **kwargs):
    """Cache the previous status of the order to track transitions in post_save."""
    if instance.pk:
        try:
            instance._old_status = Order.objects.get(pk=instance.pk).status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(pre_save, sender=Booking)
def on_booking_pre_save(sender, instance, **kwargs):
    """Cache the previous payment status of the booking to track transitions in post_save."""
    if instance.pk:
        try:
            instance._old_payment_status = Booking.objects.get(pk=instance.pk).payment_status
        except Booking.DoesNotExist:
            instance._old_payment_status = None
    else:
        instance._old_payment_status = None


# ──────────────────────────────────────────────────────────────────────
# Order signals
# ──────────────────────────────────────────────────────────────────────

@receiver(post_save, sender=Order)
def on_order_saved(sender, instance, created, **kwargs):
    """
    Post-save hook for orders.

    *If created* (brand-new order) → send order confirmation email.
    *If status transitions to CONFIRMED* → send WhatsApp confirmation.
    *If status transitions to SHIPPED* → send shipping notification email.
    """
    if created:
        _send_order_confirmation(instance)
    else:
        old_status = getattr(instance, '_old_status', None)

        # Trigger WhatsApp on confirmation
        if old_status != Order.OrderStatus.CONFIRMED and instance.status == Order.OrderStatus.CONFIRMED:
            _send_order_confirmed_whatsapp(instance)

        # Shipping notification: fire only when transitioning TO 'shipped'
        if instance.status == Order.OrderStatus.SHIPPED and old_status != Order.OrderStatus.SHIPPED:
            _send_shipping_notification(instance)


def _send_order_confirmation(order):
    """Build and dispatch the order confirmation email."""
    items = order.items.all()
    context = {
        'order': order,
        'items': items,
        'studio_name': 'Fun with Art',
        'support_email': settings.DEFAULT_FROM_EMAIL,
    }

    subject = f'Order Confirmed – Fun with Art #{order.id}'
    body_plain = render_to_string('notifications/order_confirmation.txt', context)
    body_html = render_to_string('notifications/order_confirmation.html', context)

    send_email_async(subject, body_plain, body_html, [order.contact_email])


def _send_order_confirmed_whatsapp(order):
    """Build and dispatch the order confirmation WhatsApp message."""
    try:
        phone = order.contact_phone
        variables = {
            'name': order.shipping_first_name,
            'order_id': str(order.id),
            'total_amount': f"{order.total_amount:.2f}"
        }
        send_whatsapp_async(phone, 'order_confirmed', variables)
    except Exception:
        logger.exception('Failed to trigger order confirmation WhatsApp message')


def _send_shipping_notification(order):
    """Build and dispatch the 'your order has shipped' email."""
    items = order.items.all()
    context = {
        'order': order,
        'items': items,
        'studio_name': 'Fun with Art',
        'support_email': settings.DEFAULT_FROM_EMAIL,
    }

    subject = f'Your Fun with Art order #{order.id} is on the way!'
    body_plain = render_to_string('notifications/order_shipped.txt', context)
    body_html = render_to_string('notifications/order_shipped.html', context)

    send_email_async(subject, body_plain, body_html, [order.contact_email])


# ──────────────────────────────────────────────────────────────────────
# Workshop signals
# ──────────────────────────────────────────────────────────────────────

@receiver(post_save, sender=Booking)
def on_workshop_booked(sender, instance, created, **kwargs):
    """
    Post-save hook for bookings.

    *If created* → send workshop booked email.
    *If payment_status transitions to CONFIRMED* → send WhatsApp confirmation.
    """
    if created:
        _send_workshop_booked_email(instance)
    else:
        old_payment_status = getattr(instance, '_old_payment_status', None)
        if old_payment_status != Booking.PaymentStatus.CONFIRMED and instance.payment_status == Booking.PaymentStatus.CONFIRMED:
            _send_workshop_confirmed_whatsapp(instance)


def _send_workshop_booked_email(booking):
    """Build and dispatch the workshop booking confirmation email."""
    try:
        workshop = booking.workshop
        context = {
            'booking': booking,
            'workshop': workshop,
            'user': booking.user,
            'studio_name': 'Fun with Art',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        }

        subject = f'Workshop Booked: {workshop.title} – Fun with Art'
        body_plain = render_to_string('notifications/workshop_booked.txt', context)
        body_html = render_to_string('notifications/workshop_booked.html', context)

        recipient = booking.user.email
        if not recipient:
            logger.warning('Workshop booking %s has no user email; skipping.', booking.pk)
            return

        send_email_async(subject, body_plain, body_html, [recipient])
    except Exception:
        logger.exception('Failed to send workshop booking email (non-fatal)')


def _send_workshop_confirmed_whatsapp(booking):
    """Build and dispatch the workshop booking confirmation WhatsApp message."""
    try:
        profile = getattr(booking.user, 'profile', None)
        phone = profile.phone if profile else ""
        
        if not phone:
            logger.warning(
                'Workshop booking %s user has no profile phone; skipping WhatsApp confirmation.',
                booking.pk
            )
            return

        from django.utils import timezone
        local_time = timezone.localtime(booking.updated_at)

        variables = {
            'name': booking.user.first_name or booking.user.username,
            'workshop_title': booking.workshop.title,
            'payment_date': local_time.strftime('%d-%b-%Y'),
            'payment_time': local_time.strftime('%I:%M %p')
        }
        send_whatsapp_async(phone, 'workshop_booked', variables)
    except Exception:
        logger.exception('Failed to trigger workshop confirmation WhatsApp message')
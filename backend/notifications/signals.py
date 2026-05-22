"""
Signal handlers that fire transactional emails when key business events occur.

Triggers:
    - order_placed       → order confirmation receipt
    - order_shipped      → shipping notification with tracking context
    - workshop_booked    → workshop booking confirmation
"""

import logging
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.template.loader import render_to_string

from orders.models import Order
from workshops.models import Booking

from .emails import send_email_async

logger = logging.getLogger('notifications')

# ──────────────────────────────────────────────────────────────────────
# Order signals
# ──────────────────────────────────────────────────────────────────────


@receiver(post_save, sender=Order)
def on_order_saved(sender, instance, created, **kwargs):
    """
    Post-save hook for orders.

    *If created* (brand-new order) → send order confirmation.
    *If status changed to SHIPPED* → send shipping notification.

    We check ``created`` for the confirmation email rather than using
    ``pre_save`` + ``post_save`` state tracking to keep things simple.
    """

    if created:
        _send_order_confirmation(instance)
    else:
        # Shipping notification: fire only when transitioning TO 'shipped'
        if instance.status == Order.OrderStatus.SHIPPED:
            _send_shipping_notification(instance)


def _send_order_confirmation(order):
    """Build and dispatch the order confirmation email."""
    items = order.items.all()
    context = {
        'order': order,
        'items': items,
        'studio_name': 'Udaan Studio',
        'support_email': settings.DEFAULT_FROM_EMAIL,
    }

    subject = f'Order Confirmed – Udaan Studio #{order.id}'
    body_plain = render_to_string('notifications/order_confirmation.txt', context)
    body_html = render_to_string('notifications/order_confirmation.html', context)

    send_email_async(subject, body_plain, body_html, [order.contact_email])


def _send_shipping_notification(order):
    """Build and dispatch the 'your order has shipped' email."""
    items = order.items.all()
    context = {
        'order': order,
        'items': items,
        'studio_name': 'Udaan Studio',
        'support_email': settings.DEFAULT_FROM_EMAIL,
    }

    subject = f'Your Udaan Studio order #{order.id} is on the way!'
    body_plain = render_to_string('notifications/order_shipped.txt', context)
    body_html = render_to_string('notifications/order_shipped.html', context)

    send_email_async(subject, body_plain, body_html, [order.contact_email])


# ──────────────────────────────────────────────────────────────────────
# Workshop signals
# ──────────────────────────────────────────────────────────────────────


@receiver(post_save, sender=Booking)
def on_workshop_booked(sender, instance, created, **kwargs):
    """Send workshop booking confirmation when a new Booking row is created."""
    if not created:
        return

    workshop = instance.workshop
    context = {
        'booking': instance,
        'workshop': workshop,
        'user': instance.user,
        'studio_name': 'Udaan Studio',
        'support_email': settings.DEFAULT_FROM_EMAIL,
    }

    subject = f'Workshop Booked: {workshop.title} – Udaan Studio'
    body_plain = render_to_string('notifications/workshop_booked.txt', context)
    body_html = render_to_string('notifications/workshop_booked.html', context)

    recipient = instance.user.email
    if not recipient:
        logger.warning('Workshop booking %s has no user email; skipping.', instance.pk)
        return

    send_email_async(subject, body_plain, body_html, [recipient])
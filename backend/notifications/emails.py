"""
Background email dispatcher — runs send_mail in a daemon thread so the
HTTP response is never blocked by SMTP round-trips.
"""

import threading
import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger('notifications')


def _send_mail_thread(subject, body_plain, body_html, recipient_list):
    """Internal: send email in a daemon thread, log failures."""
    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=body_plain,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
        )
        message.attach_alternative(body_html, 'text/html')
        message.send(fail_silently=False)
        logger.info(
            'Email sent — subject="%s" to=%s', subject, recipient_list,
        )
    except Exception:
        logger.exception(
            'Email failed — subject="%s" to=%s', subject, recipient_list,
        )


def send_email_async(subject, body_plain, body_html, recipient_list):
    """
    Public API: fire-and-forget email via background daemon thread.

    Usage:
        send_email_async('Welcome', plain, html, ['user@example.com'])
    """
    thread = threading.Thread(
        target=_send_mail_thread,
        args=(subject, body_plain, body_html, recipient_list),
        daemon=True,
    )
    thread.start()
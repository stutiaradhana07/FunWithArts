"""
Background email dispatcher with delivery tracking and retry mechanism.
Runs send_mail in a daemon thread so the HTTP response is never blocked by SMTP round-trips.

Features:
- Email delivery tracking via EmailDeliveryTracking model
- Automatic retry queue for failed sends
- User notification of delivery failures (stored as tracking record)
- Thread-safe fire-and-forget sending
"""

import threading
import logging
from datetime import timedelta
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from .models import EmailDeliveryTracking, EmailRetryQueue

logger = logging.getLogger('notifications')


def _send_mail_thread(subject, body_plain, body_html, recipient_list, user=None, tracking_id=None):
    """Internal: send email in a daemon thread with tracking and retry."""
    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=body_plain,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
        )
        message.attach_alternative(body_html, 'text/html')
        message.send(fail_silently=False)
        
        # Mark as sent in tracking
        if tracking_id:
            tracking = EmailDeliveryTracking.objects.get(id=tracking_id)
            tracking.mark_as_sent()
        
        logger.info(
            'Email sent — subject="%s" to=%s', subject, recipient_list,
        )
    except Exception as e:
        logger.exception(
            'Email failed — subject="%s" to=%s', subject, recipient_list,
        )
        
        # Mark as failed and queue for retry
        if tracking_id:
            try:
                tracking = EmailDeliveryTracking.objects.get(id=tracking_id)
                tracking.mark_as_failed(str(e))
                
                # Queue for retry if not exhausted
                if tracking.should_retry():
                    retry_after = min(2 ** tracking.attempt_count * 60, 3600)  # Exponential backoff
                    EmailRetryQueue.objects.create(
                        tracking=tracking,
                        scheduled_at=timezone.now() + timedelta(seconds=retry_after),
                    )
                    logger.info(
                        'Email retry queued — tracking_id=%s, attempt=%d, retry_after=%ds',
                        tracking_id,
                        tracking.attempt_count,
                        retry_after,
                    )
            except EmailDeliveryTracking.DoesNotExist:
                logger.warning('EmailDeliveryTracking record not found: %s', tracking_id)


def send_email_async(subject, body_plain, body_html, recipient_list, user=None):
    """
    Public API: fire-and-forget email via background daemon thread with tracking.
    
    Creates an EmailDeliveryTracking record for each recipient to monitor delivery.
    Automatically queues failed emails for retry with exponential backoff.

    Args:
        subject (str): Email subject
        body_plain (str): Plain text body
        body_html (str): HTML body
        recipient_list (list): List of recipient email addresses
        user (User, optional): Associated user for tracking context

    Usage:
        send_email_async(
            'Welcome',
            'Welcome to FunWithArts!',
            '<h1>Welcome</h1>',
            ['user@example.com'],
            user=request.user
        )
    """
    # Create tracking records for each recipient
    tracking_records = []
    for recipient_email in recipient_list:
        tracking = EmailDeliveryTracking.objects.create(
            recipient_email=recipient_email,
            user=user,
            subject=subject,
            body_plain=body_plain,
            body_html=body_html,
        )
        tracking_records.append(tracking)
    
    # Send in background thread
    for tracking in tracking_records:
        thread = threading.Thread(
            target=_send_mail_thread,
            args=(subject, body_plain, body_html, [tracking.recipient_email], user, tracking.id),
            daemon=True,
        )
        thread.start()


def process_email_retry_queue():
    """
    Process queued emails ready for retry.
    Should be called periodically by a Celery task or management command.
    
    Example (in a management command or scheduled task):
        from notifications.emails import process_email_retry_queue
        process_email_retry_queue()
    """
    now = timezone.now()
    pending_retries = EmailRetryQueue.objects.filter(
        scheduled_at__lte=now,
        is_processed=False,
    ).select_related('tracking')
    
    for retry in pending_retries:
        tracking = retry.tracking
        if tracking.should_retry():
            logger.info('Processing retry for tracking_id=%s (attempt %d)', tracking.id, tracking.attempt_count + 1)
            
            # Send email again
            thread = threading.Thread(
                target=_send_mail_thread,
                args=(
                    tracking.subject,
                    tracking.body_plain,
                    tracking.body_html,
                    [tracking.recipient_email],
                    tracking.user,
                    tracking.id,
                ),
                daemon=True,
            )
            thread.start()
            
            retry.is_processed = True
            retry.save()
        else:
            # No more retries needed
            retry.is_processed = True
            retry.save()
            logger.warning(
                'Email retry exhausted — tracking_id=%s, final_status=%s',
                tracking.id,
                tracking.status,
            )

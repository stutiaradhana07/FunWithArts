from django.db import models
from django.contrib.auth.models import User


class EmailDeliveryTracking(models.Model):
    """Track email delivery status and retry attempts."""
    
    class EmailStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'
        RETRY = 'retry', 'Retry Queued'
        DELIVERED = 'delivered', 'Delivered'

    recipient_email = models.EmailField(db_index=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_tracking',
    )
    subject = models.CharField(max_length=255)
    body_plain = models.TextField()
    body_html = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=EmailStatus.choices,
        default=EmailStatus.PENDING,
        db_index=True,
    )
    attempt_count = models.PositiveSmallIntegerField(default=0)
    max_retries = models.PositiveSmallIntegerField(default=3)
    last_error = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['recipient_email', 'status']),
        ]

    def __str__(self):
        return f'{self.subject} → {self.recipient_email} ({self.status})'

    def mark_as_sent(self):
        """Mark email as successfully sent."""
        from django.utils import timezone
        self.status = self.EmailStatus.SENT
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at', 'updated_at'])

    def mark_as_failed(self, error_message=None):
        """Mark email as failed and queue for retry if attempts remain."""
        self.attempt_count += 1
        if error_message:
            self.last_error = error_message
        
        if self.attempt_count < self.max_retries:
            self.status = self.EmailStatus.RETRY
        else:
            self.status = self.EmailStatus.FAILED
        
        self.save(update_fields=['status', 'attempt_count', 'last_error', 'updated_at'])

    def should_retry(self):
        """Check if email should be retried."""
        return self.status == self.EmailStatus.RETRY and self.attempt_count < self.max_retries


class EmailRetryQueue(models.Model):
    """Queue for emails waiting to be retried."""
    
    tracking = models.OneToOneField(
        EmailDeliveryTracking,
        on_delete=models.CASCADE,
        related_name='retry_queue',
    )
    scheduled_at = models.DateTimeField(db_index=True)
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f'Retry {self.tracking.id} scheduled for {self.scheduled_at}'

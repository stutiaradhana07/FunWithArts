from django.contrib import admin
from .models import EmailDeliveryTracking, EmailRetryQueue


@admin.register(EmailDeliveryTracking)
class EmailDeliveryTrackingAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'recipient_email',
        'subject_short',
        'status',
        'attempt_count',
        'sent_at',
        'created_at',
    ]
    list_filter = ['status', 'created_at', 'attempt_count']
    search_fields = ['recipient_email', 'subject', 'user__email']
    readonly_fields = [
        'id',
        'body_plain',
        'body_html',
        'last_error',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        ('Recipient Info', {
            'fields': ['id', 'recipient_email', 'user'],
        }),
        ('Email Content', {
            'fields': ['subject', 'body_plain', 'body_html'],
            'classes': ['collapse'],
        }),
        ('Status & Tracking', {
            'fields': ['status', 'attempt_count', 'max_retries', 'last_error', 'sent_at'],
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse'],
        }),
    )
    actions = ['mark_as_pending', 'mark_as_retry']

    def subject_short(self, obj):
        return obj.subject[:50] + ('...' if len(obj.subject) > 50 else '')
    subject_short.short_description = 'Subject'

    def mark_as_pending(self, request, queryset):
        count = queryset.update(status=EmailDeliveryTracking.EmailStatus.PENDING)
        self.message_user(request, f'{count} emails marked as pending.')
    mark_as_pending.short_description = 'Mark selected as pending'

    def mark_as_retry(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        
        count = 0
        for tracking in queryset:
            if tracking.attempt_count < tracking.max_retries:
                tracking.status = EmailDeliveryTracking.EmailStatus.RETRY
                tracking.save()
                
                # Create retry queue entry
                EmailRetryQueue.objects.get_or_create(
                    tracking=tracking,
                    defaults={'scheduled_at': timezone.now() + timedelta(minutes=5)},
                )
                count += 1
        
        self.message_user(request, f'{count} emails queued for retry.')
    mark_as_retry.short_description = 'Queue selected for retry'


@admin.register(EmailRetryQueue)
class EmailRetryQueueAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'tracking_subject',
        'tracking_recipient',
        'scheduled_at',
        'is_processed',
        'created_at',
    ]
    list_filter = ['is_processed', 'scheduled_at', 'created_at']
    search_fields = ['tracking__subject', 'tracking__recipient_email']
    readonly_fields = ['id', 'created_at']
    actions = ['mark_as_processed']

    def tracking_subject(self, obj):
        return obj.tracking.subject[:50]
    tracking_subject.short_description = 'Email Subject'

    def tracking_recipient(self, obj):
        return obj.tracking.recipient_email
    tracking_recipient.short_description = 'Recipient'

    def mark_as_processed(self, request, queryset):
        count = queryset.update(is_processed=True)
        self.message_user(request, f'{count} queue entries marked as processed.')
    mark_as_processed.short_description = 'Mark selected as processed'

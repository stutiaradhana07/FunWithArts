from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Order, OrderItem, PincodeRule, ShippingZone, ExchangeRequest


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'unit_price', 'quantity', 'line_total')


class PincodeRuleInline(admin.TabularInline):
    model = PincodeRule
    extra = 1


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
        'is_serviceable',
        'min_delivery_days',
        'max_delivery_days',
        'region_digit',
        'is_default_region',
    )
    list_filter = ('is_serviceable', 'is_default_region')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PincodeRuleInline]


@admin.register(PincodeRule)
class PincodeRuleAdmin(admin.ModelAdmin):
    list_display = ('value', 'rule_type', 'zone', 'priority')
    list_filter = ('rule_type', 'zone')
    search_fields = ('value', 'zone__name')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'contact_email', 'payment_method', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('contact_email', 'contact_phone', 'shipping_pincode')
    inlines = [OrderItemInline]


# ──────────────────────────────────────────────────────────────────────────────
# Exchange Request Admin
# ──────────────────────────────────────────────────────────────────────────────

def _fire_exchange_decision_email(exchange):
    """Non-blocking: fire the exchange decision notification email."""
    try:
        from notifications.emails import send_email_async
        from django.template.loader import render_to_string
        from django.conf import settings

        context = {
            'exchange': exchange,
            'order': exchange.order,
            'studio_name': 'Fun with Art',
            'support_email': settings.DEFAULT_FROM_EMAIL,
            'is_approved': exchange.status == ExchangeRequest.ExchangeStatus.APPROVED,
        }
        subject = (
            f'Exchange Request {exchange.reference_id} — '
            + ('Approved ✓' if exchange.status == ExchangeRequest.ExchangeStatus.APPROVED else 'Decision Update')
        )
        body_plain = render_to_string('notifications/exchange_decision.txt', context)
        body_html = render_to_string('notifications/exchange_decision.html', context)

        recipient_email = (
            exchange.user.email if exchange.user
            else exchange.order.contact_email
        )
        send_email_async(subject, body_plain, body_html, [recipient_email])
    except Exception:
        import logging
        logging.getLogger('notifications').exception(
            'Failed to send exchange decision email for %s', exchange.reference_id
        )


@admin.action(description='✅ Approve selected exchange requests')
def approve_exchanges(modeladmin, request, queryset):
    """Bulk approve exchange requests and notify customers."""
    updated = queryset.filter(
        status=ExchangeRequest.ExchangeStatus.PENDING_REVIEW
    ).update(status=ExchangeRequest.ExchangeStatus.APPROVED)

    # Reload to get fresh objects and fire emails
    for exchange in ExchangeRequest.objects.filter(
        pk__in=queryset.values_list('pk', flat=True),
        status=ExchangeRequest.ExchangeStatus.APPROVED,
    ):
        _fire_exchange_decision_email(exchange)

    modeladmin.message_user(
        request,
        f'{updated} exchange request(s) approved and customers notified.',
    )


@admin.action(description='❌ Reject selected exchange requests')
def reject_exchanges(modeladmin, request, queryset):
    """Bulk reject exchange requests and notify customers."""
    updated = queryset.filter(
        status=ExchangeRequest.ExchangeStatus.PENDING_REVIEW
    ).update(status=ExchangeRequest.ExchangeStatus.REJECTED)

    for exchange in ExchangeRequest.objects.filter(
        pk__in=queryset.values_list('pk', flat=True),
        status=ExchangeRequest.ExchangeStatus.REJECTED,
    ):
        _fire_exchange_decision_email(exchange)

    modeladmin.message_user(
        request,
        f'{updated} exchange request(s) rejected and customers notified.',
    )


@admin.action(description='📦 Mark selected exchanges as Completed')
def complete_exchanges(modeladmin, request, queryset):
    """Mark approved exchanges as completed (replacement dispatched)."""
    updated = queryset.filter(
        status=ExchangeRequest.ExchangeStatus.APPROVED
    ).update(status=ExchangeRequest.ExchangeStatus.COMPLETED)
    modeladmin.message_user(request, f'{updated} exchange(s) marked as completed.')


@admin.register(ExchangeRequest)
class ExchangeRequestAdmin(admin.ModelAdmin):
    list_display = (
        'reference_id',
        'order_link',
        'customer_email',
        'exchange_type',
        'status_badge',
        'created_at',
    )
    list_filter = ('status', 'exchange_type', 'created_at')
    search_fields = ('reference_id', 'order__id', 'user__email', 'order__contact_email')
    ordering = ('-created_at',)
    actions = [approve_exchanges, reject_exchanges, complete_exchanges]

    readonly_fields = (
        'reference_id',
        'order',
        'order_item',
        'user',
        'exchange_type',
        'alt_product',
        'reason',
        'video_preview',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('📋 Request Details', {
            'fields': (
                'reference_id',
                'order',
                'order_item',
                'user',
                'exchange_type',
                'alt_product',
                'reason',
                'video_preview',
            ),
        }),
        ('⚙️ Admin Decision', {
            'fields': ('status', 'admin_notes'),
        }),
        ('🕐 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def order_link(self, obj):
        return format_html(
            '<a href="/admin/orders/order/{}/change/">Order #{}</a>',
            obj.order_id,
            obj.order_id,
        )
    order_link.short_description = 'Order'

    def customer_email(self, obj):
        if obj.user:
            return obj.user.email
        return obj.order.contact_email
    customer_email.short_description = 'Customer'

    def status_badge(self, obj):
        colours = {
            ExchangeRequest.ExchangeStatus.PENDING_REVIEW: '#d97706',
            ExchangeRequest.ExchangeStatus.APPROVED: '#16a34a',
            ExchangeRequest.ExchangeStatus.REJECTED: '#dc2626',
            ExchangeRequest.ExchangeStatus.COMPLETED: '#2563eb',
        }
        colour = colours.get(obj.status, '#6b7280')
        return format_html(
            '<span style="color:{};font-weight:700;">{}</span>',
            colour,
            obj.get_status_display(),
        )
    status_badge.short_description = 'Status'

    def video_preview(self, obj):
        if obj.unboxing_video:
            return format_html(
                '<a href="{}" target="_blank" style="color:#d7a88d;font-weight:bold;">▶ View Unboxing Video</a>',
                obj.unboxing_video.url,
            )
        return '—'
    video_preview.short_description = 'Unboxing Video'


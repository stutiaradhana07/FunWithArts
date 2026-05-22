from django.contrib import admin
from .models import Payment, Refund


class RefundInline(admin.TabularInline):
    model = Refund
    extra = 0
    readonly_fields = ('razorpay_refund_id', 'amount', 'status', 'created_at', 'processed_at')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'order', 
        'razorpay_order_id', 
        'razorpay_payment_id',
        'amount', 
        'status', 
        'payment_method',
        'created_at'
    )
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = (
        'order__id', 
        'razorpay_order_id', 
        'razorpay_payment_id',
        'order__contact_email'
    )
    readonly_fields = (
        'razorpay_order_id', 
        'razorpay_payment_id', 
        'razorpay_signature',
        'created_at', 
        'updated_at', 
        'captured_at'
    )
    inlines = [RefundInline]
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.status != Payment.PaymentStatus.PENDING:
            readonly.extend(['amount', 'currency', 'order'])
        return readonly


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'payment', 
        'razorpay_refund_id', 
        'amount', 
        'status', 
        'created_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = (
        'payment__order__id', 
        'razorpay_refund_id',
        'payment__razorpay_payment_id'
    )
    readonly_fields = (
        'razorpay_refund_id',
        'payment',
        'amount',
        'created_at',
        'processed_at'
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.status != Refund.RefundStatus.PENDING:
            readonly.extend(['reason'])
        return readonly

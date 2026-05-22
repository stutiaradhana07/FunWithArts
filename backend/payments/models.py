from django.db import models
from django.contrib.auth.models import User
from orders.models import Order


class Payment(models.Model):
    """Stores payment information for orders"""
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CREATED = 'created', 'Created'
        CAPTURED = 'captured', 'Captured'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'
        CANCELLED = 'cancelled', 'Cancelled'

    class PaymentMethod(models.TextChoices):
        CARD = 'card', 'Card'
        UPI = 'upi', 'UPI'
        NETBANKING = 'netbanking', 'Net Banking'
        WALLET = 'wallet', 'Wallet'
        COD = 'cod', 'Cash on Delivery'

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    razorpay_order_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # in INR
    currency = models.CharField(max_length=3, default='INR')
    
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    captured_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Payment for Order #{self.order.id} - {self.status}'
    
    def mark_captured(self, razorpay_payment_id=None, razorpay_signature=None):
        """Mark payment as captured and update order status"""
        from django.utils import timezone
        
        self.status = self.PaymentStatus.CAPTURED
        self.captured_at = timezone.now()
        
        if razorpay_payment_id:
            self.razorpay_payment_id = razorpay_payment_id
        if razorpay_signature:
            self.razorpay_signature = razorpay_signature
            
        self.save()
        
        # Update order status
        self.order.status = Order.OrderStatus.CONFIRMED
        self.order.save()


class Refund(models.Model):
    """Stores refund information for payments"""
    
    class RefundStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSED = 'processed', 'Processed'
        FAILED = 'failed', 'Failed'

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    razorpay_refund_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField(blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=RefundStatus.choices,
        default=RefundStatus.PENDING
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Refund for Payment #{self.payment.id} - {self.status}'

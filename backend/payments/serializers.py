from rest_framework import serializers
from .models import Payment, Refund


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'order',
            'razorpay_order_id',
            'razorpay_payment_id',
            'amount',
            'currency',
            'status',
            'payment_method',
            'created_at',
            'captured_at',
        ]
        read_only_fields = [
            'razorpay_order_id',
            'razorpay_payment_id',
            'created_at',
            'captured_at',
        ]


class PaymentCreateSerializer(serializers.Serializer):
    """Serializer for creating Razorpay order"""
    order_id = serializers.IntegerField()
    
    def validate_order_id(self, value):
        from orders.models import Order
        
        try:
            order = Order.objects.get(id=value)
            if hasattr(order, 'payment'):
                raise serializers.ValidationError("Payment already initiated for this order")
            return value
        except Order.DoesNotExist:
            raise serializers.ValidationError("Invalid order ID")


class RazorpayOrderSerializer(serializers.Serializer):
    """Serializer for Razorpay order response"""
    razorpay_order_id = serializers.CharField()
    amount = serializers.IntegerField()
    currency = serializers.CharField()
    receipt = serializers.CharField()


class PaymentVerificationSerializer(serializers.Serializer):
    """Serializer for verifying Razorpay payment"""
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()


class RefundSerializer(serializers.ModelSerializer):
    """Serializer for Refund model"""
    
    class Meta:
        model = Refund
        fields = [
            'id',
            'payment',
            'razorpay_refund_id',
            'amount',
            'reason',
            'status',
            'created_at',
            'processed_at',
        ]
        read_only_fields = [
            'razorpay_refund_id',
            'created_at',
            'processed_at',
        ]


class RefundCreateSerializer(serializers.Serializer):
    """Serializer for creating refund"""
    payment_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_payment_id(self, value):
        try:
            payment = Payment.objects.get(id=value)
            if payment.status != Payment.PaymentStatus.CAPTURED:
                raise serializers.ValidationError("Payment must be captured before refund")
            return value
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Invalid payment ID")

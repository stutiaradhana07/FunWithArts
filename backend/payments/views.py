import razorpay
import json
import hmac
import hashlib
from decimal import Decimal
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from orders.models import Order
from .models import Payment, Refund
from .serializers import (
    PaymentCreateSerializer, 
    RazorpayOrderSerializer,
    PaymentVerificationSerializer,
    PaymentSerializer,
    RefundCreateSerializer,
    RefundSerializer
)


# Initialize Razorpay client
def get_razorpay_client():
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def create_payment_order(request):
    """
    Create a Razorpay order for given order (supports guest & authenticated users).
    POST /api/payments/create-order/
    Guests: Include order_id from guest order.
    Authenticated: Can pay for own orders or guest orders.
    """
    serializer = PaymentCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    order_id = serializer.validated_data['order_id']
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response(
            {'error': 'Order not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Verify order belongs to user or is guest order
    if order.user and order.user != request.user:
        return Response(
            {'error': 'You can only create payment for your own orders'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Guest order: verify caller knows the contact email on the order
    if order.user is None:
        contact_email = request.data.get('contact_email', '')
        if not contact_email or contact_email.strip().lower() != (order.contact_email or '').strip().lower():
            return Response(
                {'error': 'Email verification required for guest orders'},
                status=status.HTTP_403_FORBIDDEN,
            )
    
    try:
        # Check for an existing CREATED payment (retry safety)
        existing = Payment.objects.filter(
            order=order, status=Payment.PaymentStatus.CREATED
        ).first()
        if existing:
            payment = existing
        else:
            # Create Razorpay order
            client = get_razorpay_client()
            razorpay_order = client.order.create({
                'amount': int(order.total_amount * 100),  # Convert to paise
                'currency': 'INR',
                'receipt': f'order_{order.id}',
                'payment_capture': 1
            })
            
            # Create payment record
            payment = Payment.objects.create(
                order=order,
                razorpay_order_id=razorpay_order['id'],
                amount=order.total_amount,
                currency='INR',
                status=Payment.PaymentStatus.CREATED
            )
        
        response_data = {
            'razorpay_order_id': payment.razorpay_order_id,
            'amount': int(order.total_amount * 100),
            'currency': 'INR',
            'receipt': f'order_{order.id}',
            'key_id': settings.RAZORPAY_KEY_ID,
            'name': 'Fun with Art',
            'description': f'Payment for Order #{order.id}',
            'prefill': {
                'email': order.contact_email,
                'contact': order.contact_phone
            }
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to create payment order: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_payment(request):
    """
    Verify Razorpay payment and update order status (supports guest & authenticated users).
    POST /api/payments/verify/
    """
    serializer = PaymentVerificationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    razorpay_order_id = serializer.validated_data['razorpay_order_id']
    razorpay_payment_id = serializer.validated_data['razorpay_payment_id']
    razorpay_signature = serializer.validated_data['razorpay_signature']
    
    try:
        # Get payment record
        payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
        
        # Verify payment signature
        client = get_razorpay_client()
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            client.utility.verify_payment_signature(params_dict)
        except razorpay.errors.SignatureVerificationError:
            return Response(
                {'error': 'Invalid payment signature'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Fetch payment details to get payment method
        payment_details = client.payment.fetch(razorpay_payment_id)
        
        # Update payment record
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.payment_method = payment_details['method']
        payment.mark_captured()
        
        return Response({
            'message': 'Payment verified successfully',
            'payment_id': payment.id,
            'order_id': payment.order.id,
            'status': payment.status
        })
        
    except Payment.DoesNotExist:
        return Response(
            {'error': 'Payment record not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Payment verification failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_detail(request, payment_id):
    """
    Get payment details
    GET /api/payments/{payment_id}/
    """
    try:
        payment = Payment.objects.get(id=payment_id)
        
        # Verify user owns this payment
        if payment.order.user and payment.order.user != request.user:
            return Response(
                {'error': 'You can only view your own payments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = PaymentSerializer(payment)
        return Response(serializer.data)
        
    except Payment.DoesNotExist:
        return Response(
            {'error': 'Payment not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_refund(request):
    """
    Create a refund for a payment
    POST /api/payments/refund/
    """
    serializer = RefundCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    payment_id = serializer.validated_data['payment_id']
    amount = serializer.validated_data['amount']
    reason = serializer.validated_data.get('reason', '')
    
    try:
        payment = Payment.objects.get(id=payment_id)
        
        # Verify user owns this payment
        if payment.order.user and payment.order.user != request.user:
            return Response(
                {'error': 'You can only refund your own payments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create refund record
        refund = Refund.objects.create(
            payment=payment,
            amount=amount,
            reason=reason
        )
        
        try:
            # Process refund with Razorpay
            client = get_razorpay_client()
            razorpay_refund = client.payment.refund(
                payment.razorpay_payment_id,
                {
                    'amount': int(amount * 100),  # Convert to paise
                    'notes': {
                        'reason': reason
                    }
                }
            )
            
            refund.razorpay_refund_id = razorpay_refund['id']
            refund.status = Refund.RefundStatus.PROCESSED
            refund.processed_at = timezone.now()
            refund.save()
            
            return Response({
                'message': 'Refund processed successfully',
                'refund_id': refund.id,
                'razorpay_refund_id': razorpay_refund['id'],
                'amount': float(amount)
            })
            
        except Exception as e:
            refund.status = Refund.RefundStatus.FAILED
            refund.save()
            return Response(
                {'error': f'Refund processing failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Payment.DoesNotExist:
        return Response(
            {'error': 'Payment not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """
    Handle Razorpay webhooks for payment events
    POST /api/payments/webhook/
    """
    try:
        # Get webhook signature
        webhook_signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE')
        if not webhook_signature:
            return JsonResponse({'error': 'Missing signature'}, status=400)
        
        # Verify webhook signature
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        payload = request.body
        
        expected_signature = hmac.new(
            webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(webhook_signature, expected_signature):
            return JsonResponse({'error': 'Invalid signature'}, status=400)
        
        # Parse webhook event
        event_data = json.loads(payload)
        event_type = event_data['event']
        
        # Handle payment events
        if event_type == 'payment.captured':
            handle_payment_captured(event_data)
        elif event_type == 'payment.failed':
            handle_payment_failed(event_data)
        elif event_type == 'refund.processed':
            handle_refund_processed(event_data)
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        return JsonResponse(
            {'error': f'Webhook processing failed: {str(e)}'},
            status=500
        )


def handle_payment_captured(event_data):
    """Handle payment.captured webhook event"""
    payment_entity = event_data['payload']['payment']['entity']
    razorpay_order_id = payment_entity['order_id']
    razorpay_payment_id = payment_entity['id']
    
    try:
        payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
        payment.razorpay_payment_id = razorpay_payment_id
        payment.payment_method = payment_entity['method']
        payment.mark_captured()
    except Payment.DoesNotExist:
        pass  # Payment record not found, ignore


def handle_payment_failed(event_data):
    """Handle payment.failed webhook event"""
    payment_entity = event_data['payload']['payment']['entity']
    razorpay_order_id = payment_entity['order_id']
    
    try:
        payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
        payment.status = Payment.PaymentStatus.FAILED
        payment.save()
        
        # Update order status to cancelled
        payment.order.status = Order.OrderStatus.CANCELLED
        payment.order.save()
    except Payment.DoesNotExist:
        pass  # Payment record not found, ignore


def handle_refund_processed(event_data):
    """Handle refund.processed webhook event"""
    refund_entity = event_data['payload']['refund']['entity']
    razorpay_payment_id = refund_entity['payment_id']
    razorpay_refund_id = refund_entity['id']
    
    try:
        payment = Payment.objects.get(razorpay_payment_id=razorpay_payment_id)
        refund = Refund.objects.get(payment=payment, razorpay_refund_id=razorpay_refund_id)
        refund.status = Refund.RefundStatus.PROCESSED
        refund.processed_at = timezone.now()
        refund.save()
    except (Payment.DoesNotExist, Refund.DoesNotExist):
        pass  # Records not found, ignore

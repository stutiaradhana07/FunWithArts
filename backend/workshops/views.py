import hmac
import hashlib
import json
import razorpay
from datetime import date, timedelta
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Workshop, Booking
from .serializers import (
    WorkshopSerializer,
    BookingSerializer,
    InitiateWorkshopPaymentSerializer,
    VerifyWorkshopPaymentSerializer,
)


@api_view(['GET'])
def workshop_list(request):
    workshops = Workshop.objects.filter(
        is_active=True, date__gte=date.today()
    ).order_by('date', 'time')
    serializer = WorkshopSerializer(workshops, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def workshop_detail(request, pk):
    workshop = get_object_or_404(Workshop, pk=pk)
    serializer = WorkshopSerializer(workshop, context={'request': request})
    return Response(serializer.data)


# ──────────────────────────────────────────────
#  Payment-backed workshop booking
# ──────────────────────────────────────────────

PENDING_BOOKING_EXPIRY_MINUTES = 30


def _get_razorpay_client():
    """Reuse the Razorpay client factory from payments app."""
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


def _release_expired_pending_bookings(workshop):
    """Release slots held by pending bookings older than the expiry window."""
    cutoff = timezone.now() - timedelta(minutes=PENDING_BOOKING_EXPIRY_MINUTES)
    expired = Booking.objects.filter(
        workshop=workshop,
        payment_status=Booking.PaymentStatus.PENDING,
        booking_date__lt=cutoff,
    )
    count = expired.count()
    if count:
        total_seats = sum(b.seats for b in expired)
        expired.update(payment_status=Booking.PaymentStatus.FAILED)
        workshop.available_slots += total_seats
        workshop.save(update_fields=['available_slots'])
    return count


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_workshop_payment(request):
    """
    Reserve workshop seats and create a Razorpay order.
    POST /api/workshops/{workshop_id}/initiate-payment/
    
    Request body: { "workshop_id": 5, "seats": 2 }
    Response:     { razorpay_order_id, amount, currency, key_id, booking_id, ... }
    """
    serializer = InitiateWorkshopPaymentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    workshop = serializer.workshop
    seats = serializer.validated_data['seats']

    with transaction.atomic():
        # Lock the workshop row to prevent race conditions
        workshop = Workshop.objects.select_for_update().get(pk=workshop.pk)

        # Release expired pending bookings so their slots are freed
        _release_expired_pending_bookings(workshop)

        # Re-validate availability under lock
        if seats > workshop.available_slots:
            return Response(
                {'error': f'Only {workshop.available_slots} seat(s) remaining.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Block duplicate CONFIRMED bookings for the same workshop
        already_confirmed = Booking.objects.filter(
            user=request.user,
            workshop=workshop,
            payment_status=Booking.PaymentStatus.CONFIRMED,
        ).exists()
        if already_confirmed:
            return Response(
                {'error': 'You already have a confirmed booking for this workshop.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Reserve slots (mark as pending — not deducted yet)
        workshop.available_slots -= seats
        workshop.save(update_fields=['available_slots'])

        # Create pending booking
        booking = Booking.objects.create(
            user=request.user,
            workshop=workshop,
            seats=seats,
            payment_status=Booking.PaymentStatus.PENDING,
        )

    try:
        client = _get_razorpay_client()
        receipt_id = f'ws_{workshop.id}_{booking.id}'
        razorpay_order = client.order.create({
            'amount': int(workshop.price * seats * 100),  # paise
            'currency': 'INR',
            'receipt': receipt_id,
            'payment_capture': 1,
            'notes': {
                'workshop_id': str(workshop.id),
                'booking_id': str(booking.id),
            },
        })
    except Exception as e:
        # Rollback slot reservation on Razorpay failure
        with transaction.atomic():
            w = Workshop.objects.select_for_update().get(pk=workshop.pk)
            w.available_slots += seats
            w.save(update_fields=['available_slots'])
        booking.payment_status = Booking.PaymentStatus.FAILED
        booking.save(update_fields=['payment_status'])
        return Response(
            {'error': f'Payment gateway error: {str(e)}'},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    booking.razorpay_order_id = razorpay_order['id']
    booking.save(update_fields=['razorpay_order_id'])

    return Response({
        'booking_id': booking.id,
        'razorpay_order_id': razorpay_order['id'],
        'amount': razorpay_order['amount'],
        'currency': razorpay_order['currency'],
        'key_id': settings.RAZORPAY_KEY_ID,
        'name': 'Fun with Art',
        'description': f'{workshop.title} — {seats} seat(s)',
        'prefill': {
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
        },
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_workshop_payment(request):
    """
    Verify Razorpay signature and confirm the booking.
    POST /api/workshops/payment/verify/
    
    Request: { razorpay_order_id, razorpay_payment_id, razorpay_signature }
    """
    serializer = VerifyWorkshopPaymentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    razorpay_order_id   = serializer.validated_data['razorpay_order_id']
    razorpay_payment_id = serializer.validated_data['razorpay_payment_id']
    razorpay_signature  = serializer.validated_data['razorpay_signature']

    try:
        booking = Booking.objects.select_related('workshop').get(
            razorpay_order_id=razorpay_order_id,
            user=request.user,
        )
    except Booking.DoesNotExist:
        return Response(
            {'error': 'Booking not found for this order.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if booking.payment_status == Booking.PaymentStatus.CONFIRMED:
        return Response({
            'message': 'Payment already confirmed.',
            'booking': BookingSerializer(booking).data,
        })

    # Verify signature with Razorpay
    client = _get_razorpay_client()
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        })
    except razorpay.errors.SignatureVerificationError:
        return Response(
            {'error': 'Invalid payment signature.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Mark booking confirmed — slots already deducted at initiation
    booking.razorpay_payment_id = razorpay_payment_id
    booking.razorpay_signature = razorpay_signature
    booking.payment_status = Booking.PaymentStatus.CONFIRMED
    booking.save(update_fields=[
        'razorpay_payment_id', 'razorpay_signature', 'payment_status', 'updated_at',
    ])

    return Response({
        'message': 'Payment verified — booking confirmed!',
        'booking': BookingSerializer(booking).data,
    })


# ──────────────────────────────────────────────
#  Razorpay webhook — production fallback
# ──────────────────────────────────────────────

@csrf_exempt
@require_POST
def workshop_razorpay_webhook(request):
    """
    Handle Razorpay webhook events for workshop bookings.
    POST /api/workshops/payment/webhook/

    Fallback: if the browser closes before the frontend verify-payment
    callback fires, Razorpay will POST here so we can finalise the booking.

    Events handled:
      - payment.captured → mark booking CONFIRMED
      - payment.failed   → mark booking FAILED + release reserved slots
    """
    webhook_signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE')
    if not webhook_signature:
        return JsonResponse({'error': 'Missing signature'}, status=400)

    # Verify HMAC-SHA256 signature
    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
    payload = request.body

    expected_signature = hmac.new(
        webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(webhook_signature, expected_signature):
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    try:
        event_data = json.loads(payload)
        event_type = event_data.get('event', '')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

    try:
        if event_type == 'payment.captured':
            _handle_workshop_payment_captured(event_data)
        elif event_type == 'payment.failed':
            _handle_workshop_payment_failed(event_data)
        # payment.authorized, refund.*, etc. are handled elsewhere or ignored
    except Exception as e:
        return JsonResponse(
            {'error': f'Webhook processing failed: {str(e)}'},
            status=500,
        )

    return JsonResponse({'status': 'ok'})


def _handle_workshop_payment_captured(event_data):
    """
    payment.captured: the customer successfully paid.

    Look up the booking by razorpay_order_id and mark it CONFIRMED.
    The frontend verify-payment endpoint may have already done this — if
    the booking is already CONFIRMED we are a no-op (idempotent).
    """
    payment_entity = event_data['payload']['payment']['entity']
    razorpay_order_id = payment_entity['order_id']
    razorpay_payment_id = payment_entity['id']

    try:
        booking = Booking.objects.select_related('workshop').get(
            razorpay_order_id=razorpay_order_id,
        )
    except Booking.DoesNotExist:
        return  # Not a workshop booking — ignore

    if booking.payment_status == Booking.PaymentStatus.CONFIRMED:
        return  # Already confirmed by frontend callback — idempotent

    booking.razorpay_payment_id = razorpay_payment_id
    booking.payment_status = Booking.PaymentStatus.CONFIRMED
    booking.save(update_fields=['razorpay_payment_id', 'payment_status', 'updated_at'])


def _handle_workshop_payment_failed(event_data):
    """
    payment.failed: the payment attempt was declined or abandoned.

    Mark the booking FAILED and release the reserved seats back to
    the workshop's available pool.
    """
    payment_entity = event_data['payload']['payment']['entity']
    razorpay_order_id = payment_entity['order_id']

    try:
        booking = Booking.objects.select_related('workshop').get(
            razorpay_order_id=razorpay_order_id,
        )
    except Booking.DoesNotExist:
        return

    # Only transition PENDING bookings — CONFIRMED ones stay
    if booking.payment_status != Booking.PaymentStatus.PENDING:
        return

    with transaction.atomic():
        workshop = Workshop.objects.select_for_update().get(pk=booking.workshop_id)
        workshop.available_slots += booking.seats
        workshop.save(update_fields=['available_slots'])

    booking.payment_status = Booking.PaymentStatus.FAILED
    booking.save(update_fields=['payment_status', 'updated_at'])


# ──────────────────────────────────────────────
#  My Bookings — authenticated user's workshop bookings
# ──────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_bookings(request):
    """
    Return all workshop bookings for the authenticated user,
    newest first, with nested workshop details.
    """
    bookings = (
        Booking.objects
        .filter(user=request.user)
        .select_related('workshop')
        .order_by('-booking_date')
    )
    serializer = BookingSerializer(bookings, many=True, context={'request': request})
    return Response(serializer.data)

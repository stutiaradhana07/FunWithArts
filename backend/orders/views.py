import razorpay
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from .delivery import lookup_pincode
from .models import Order, ExchangeRequest
from .serializers import (
    GuestOrderLookupSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    ExchangeRequestCreateSerializer,
    ExchangeRequestSerializer,
)


ORDER_FILTER_FIELDS = ['status']
ORDER_ORDERING_FIELDS = ['created_at', 'total_amount']


@api_view(['GET', 'POST'])
def order_list_create(request):
    """
    GET  /api/orders/?status=shipped&ordering=-created_at&page=2
         Paginated (10/page), filterable by status, orderable by date/amount.
         Requires authentication — users only see their own orders.
    POST /api/orders/ → Create a new order (guest or authenticated).
    """
    if request.method == 'POST':
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user if request.user.is_authenticated else None
        order = serializer.save(user=user)
        output = OrderSerializer(order)
        return Response(output.data, status=status.HTTP_201_CREATED)

    # GET — requires auth
    if not request.user.is_authenticated:
        return Response(
            {'error': 'Authentication required to view order history.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    qs = Order.objects.filter(user=request.user).prefetch_related('items')

    # Apply status filtering (same as DjangoFilterBackend with filterset_fields=['status'])
    status_param = request.query_params.get('status', '').strip()
    if status_param:
        qs = qs.filter(status=status_param)

    # Apply ordering (same as OrderingFilter with ordering_fields=['created_at','total_amount'])
    ordering_param = request.query_params.get('ordering', '-created_at').strip()
    allowed_ordering = {
        'created_at', '-created_at',
        'total_amount', '-total_amount',
    }
    if ordering_param in allowed_ordering:
        qs = qs.order_by(ordering_param)
    else:
        qs = qs.order_by('-created_at')

    # Paginate (PageNumberPagination, 10 per page)
    paginator = PageNumberPagination()
    paginator.page_size = 10
    page = paginator.paginate_queryset(qs, request)
    serializer = OrderSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, pk):
    """
    GET /api/orders/<id>/ → Retrieve a specific order.
    - Authenticated users: Can view their own orders or staff can view any.
    - Guest users: Cannot access this endpoint (use guest_order_lookup instead).
    """
    qs = Order.objects.prefetch_related('items')
    if request.user.is_staff:
        order = get_object_or_404(qs, pk=pk)
    else:
        order = get_object_or_404(qs, pk=pk, user=request.user)
    return Response(OrderSerializer(order).data)


@api_view(['GET'])
def delivery_check(request):
    pincode = request.query_params.get('pincode', '').strip()

    if not pincode.isdigit() or len(pincode) != 6:
        return Response(
            {'error': 'Invalid pincode. Please provide a 6-digit pincode.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if pincode[0] == '0':
        return Response(
            {'error': 'Invalid pincode. Indian pincodes do not start with 0.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = lookup_pincode(pincode)
    return Response(result.as_dict())


@api_view(['GET'])
@permission_classes([AllowAny])
def guest_order_lookup(request):
    """
    GET /api/orders/lookup/?contact_email=&order_id=
    Allows guests (or anyone) to look up an order by email + order ID.
    No authentication required.
    """
    serializer = GuestOrderLookupSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    contact_email = serializer.validated_data['contact_email']
    order_id = serializer.validated_data['order_id']

    order = get_object_or_404(
        Order.objects.prefetch_related('items'),
        pk=order_id,
        contact_email__iexact=contact_email,
    )

    return Response(OrderSerializer(order).data)


# ──────────────────────────────────────────────────────────────────────────────
# Exchange Request Views
# ──────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def exchange_list_create(request):
    """
    GET  /api/exchanges/
         Returns all exchange requests for the authenticated user (newest first).

    POST /api/exchanges/
         Submit a new exchange request.
         Expects multipart/form-data with:
           - order_id (int)
           - order_item_id (int, optional)
           - exchange_type: 'same' | 'other'
           - alt_product_id (int, required if exchange_type='other')
           - reason (str, min 20 chars)
           - unboxing_video (file, MP4/MOV/WEBM, max 500 MB)
           - confirm_authentic / confirm_review / confirm_policy (bool)
    """
    if request.method == 'POST':
        serializer = ExchangeRequestCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        exchange = serializer.save()
        return Response(
            ExchangeRequestSerializer(exchange, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    # GET — list current user's exchange requests
    qs = (
        ExchangeRequest.objects
        .filter(user=request.user)
        .select_related('order', 'order_item', 'alt_product')
        .order_by('-created_at')
    )

    paginator = PageNumberPagination()
    paginator.page_size = 10
    page = paginator.paginate_queryset(qs, request)
    serializer = ExchangeRequestSerializer(page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def exchange_detail(request, pk):
    """
    GET /api/exchanges/<id>/
    Returns the status of a specific exchange request.
    Authenticated owners can view their own; staff can view any.
    """
    if request.user.is_staff:
        exchange = get_object_or_404(
            ExchangeRequest.objects.select_related('order', 'order_item', 'alt_product'),
            pk=pk,
        )
    else:
        exchange = get_object_or_404(
            ExchangeRequest.objects.select_related('order', 'order_item', 'alt_product'),
            pk=pk,
            user=request.user,
        )
    return Response(ExchangeRequestSerializer(exchange, context={'request': request}).data)


def _get_razorpay_client():
    return razorpay.Client(
        auth=(getattr(settings, 'RAZORPAY_KEY_ID', ''), getattr(settings, 'RAZORPAY_KEY_SECRET', ''))
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def exchange_create_payment_order(request, pk):
    """
    POST /api/exchanges/<pk>/create-payment-order/
    Creates a Razorpay order for the price difference on an exchange request.
    Only valid if amount_to_pay > 0 and payment_status != 'paid'.
    """
    if request.user.is_staff:
        exchange = get_object_or_404(
            ExchangeRequest.objects.select_related('order', 'order_item', 'alt_product'),
            pk=pk,
        )
    else:
        exchange = get_object_or_404(
            ExchangeRequest.objects.select_related('order', 'order_item', 'alt_product'),
            pk=pk,
            user=request.user,
        )

    if exchange.payment_status == 'paid':
        return Response(
            {'error': 'Payment has already been completed for this exchange request.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if exchange.amount_to_pay <= 0:
        return Response(
            {'error': 'No payment is required for this exchange.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    amount_paise = int(exchange.amount_to_pay * 100)

    try:
        client = _get_razorpay_client()
        razorpay_order = client.order.create({
            'amount': amount_paise,
            'currency': 'INR',
            'receipt': f'exchange_{exchange.id}',
            'payment_capture': 1,
        })
        exchange.razorpay_order_id = razorpay_order['id']
        exchange.save(update_fields=['razorpay_order_id', 'updated_at'])

        return Response({
            'razorpay_order_id': razorpay_order['id'],
            'amount': amount_paise,
            'currency': 'INR',
            'key_id': getattr(settings, 'RAZORPAY_KEY_ID', ''),
            'exchange_id': exchange.id,
            'reference_id': exchange.reference_id,
            'amount_to_pay': str(exchange.amount_to_pay),
            'name': 'Fun with Art',
            'description': f'Price difference for Exchange {exchange.reference_id}',
            'prefill': {
                'email': exchange.order.contact_email or request.user.email or '',
                'contact': exchange.order.contact_phone or '',
            },
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(
            {'error': f'Failed to create payment order: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def exchange_verify_payment(request, pk):
    """
    POST /api/exchanges/<pk>/verify-payment/
    Verifies the Razorpay payment signature for an exchange request.
    Expects { razorpay_order_id, razorpay_payment_id, razorpay_signature }.
    """
    if request.user.is_staff:
        exchange = get_object_or_404(ExchangeRequest, pk=pk)
    else:
        exchange = get_object_or_404(ExchangeRequest, pk=pk, user=request.user)

    razorpay_order_id = request.data.get('razorpay_order_id')
    razorpay_payment_id = request.data.get('razorpay_payment_id')
    razorpay_signature = request.data.get('razorpay_signature')

    if not (razorpay_order_id and razorpay_payment_id and razorpay_signature):
        return Response(
            {'error': 'razorpay_order_id, razorpay_payment_id, and razorpay_signature are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    client = _get_razorpay_client()
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        })
    except Exception:
        return Response(
            {'error': 'Invalid payment signature.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    exchange.razorpay_payment_id = razorpay_payment_id
    exchange.razorpay_signature = razorpay_signature
    exchange.payment_status = 'paid'
    exchange.save(update_fields=['razorpay_payment_id', 'razorpay_signature', 'payment_status', 'updated_at'])

    return Response({
        'message': 'Exchange payment verified successfully.',
        'exchange_id': exchange.id,
        'reference_id': exchange.reference_id,
        'payment_status': exchange.payment_status,
    })

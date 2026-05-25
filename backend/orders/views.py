from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from .delivery import lookup_pincode
from .models import Order
from .serializers import (
    GuestOrderLookupSerializer,
    OrderCreateSerializer,
    OrderSerializer,
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
    if request.user.is_staff:
        order = get_object_or_404(Order, pk=pk)
    else:
        order = get_object_or_404(Order, pk=pk, user=request.user)
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

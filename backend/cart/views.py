from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from products.models import Product
from .models import Cart, CartItem
from .serializers import (
    AddToCartSerializer,
    CartSerializer,
    MergeCartSerializer,
    UpdateCartItemSerializer,
)


def _get_or_create_cart(request):
    """Resolve the correct cart for the current request context."""
    user = request.user if request.user.is_authenticated else None
    session_id = request.query_params.get('session_id') or request.data.get('session_id')
    return Cart.get_or_create_for_request(user, session_id)


@api_view(['GET'])
def cart_detail(request):
    """
    GET /api/cart/ — Retrieve the current cart.
    Pass ?session_id= for guest carts.
    """
    cart = _get_or_create_cart(request)
    if cart is None:
        return Response({'error': 'session_id query parameter required for guest carts.'},
                        status=status.HTTP_400_BAD_REQUEST)
    return Response(CartSerializer(cart).data)


@api_view(['POST'])
def cart_add_item(request):
    """
    POST /api/cart/add/ — Add an item to the cart.
    Body: { "product_id": 1, "quantity": 2, "session_id": "..." }
    """
    cart = _get_or_create_cart(request)
    if cart is None:
        return Response({'error': 'session_id required for guest carts.'},
                        status=status.HTTP_400_BAD_REQUEST)

    serializer = AddToCartSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    product_id = serializer.validated_data['product_id']
    qty = serializer.validated_data['quantity']
    purchase_option = serializer.validated_data.get('purchase_option', 'individual')
    product = get_object_or_404(Product, id=product_id, is_available=True)

    if product.stock < qty:
        return Response({'error': f'Only {product.stock} units available.'},
                        status=status.HTTP_400_BAD_REQUEST)

    if purchase_option == 'set' and not product.has_set_option:
        return Response({'error': f"Product '{product.name}' does not have a set buying option."},
                        status=status.HTTP_400_BAD_REQUEST)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        purchase_option=purchase_option,
        defaults={'quantity': qty},
    )
    if not created:
        item.quantity += qty
        item.save(update_fields=['quantity'])

    return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['PATCH'])
def cart_update_item(request, item_id):
    """
    PATCH /api/cart/items/<item_id>/ — Update quantity.
    Body: { "quantity": 3, "session_id": "..." }
    Set quantity=0 to remove the item.
    """
    cart = _get_or_create_cart(request)
    if cart is None:
        return Response({'error': 'session_id required for guest carts.'},
                        status=status.HTTP_400_BAD_REQUEST)

    item = get_object_or_404(CartItem, id=item_id, cart=cart)

    serializer = UpdateCartItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    new_qty = serializer.validated_data['quantity']

    if new_qty == 0:
        item.delete()
    else:
        if item.product.stock < new_qty:
            return Response({'error': f'Only {item.product.stock} units available.'},
                            status=status.HTTP_400_BAD_REQUEST)
        item.quantity = new_qty
        item.save(update_fields=['quantity'])

    return Response(CartSerializer(cart).data)


@api_view(['DELETE'])
def cart_remove_item(request, item_id):
    """
    DELETE /api/cart/items/<item_id>/ — Remove an item from the cart.
    Pass ?session_id= for guest carts.
    """
    cart = _get_or_create_cart(request)
    if cart is None:
        return Response({'error': 'session_id required for guest carts.'},
                        status=status.HTTP_400_BAD_REQUEST)

    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    return Response(CartSerializer(cart).data)


@api_view(['POST'])
def cart_clear(request):
    """
    POST /api/cart/clear/ — Remove all items from the cart.
    Body (optional): { "session_id": "..." }
    """
    cart = _get_or_create_cart(request)
    if cart is None:
        return Response({'error': 'session_id required for guest carts.'},
                        status=status.HTTP_400_BAD_REQUEST)

    cart.items.all().delete()
    return Response(CartSerializer(cart).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cart_merge(request):
    """
    POST /api/cart/merge/ — Merge an anonymous guest cart into the authenticated user's cart.
    Body: { "session_id": "abc123" }
    - Items from the guest cart are merged into the user's cart.
    - Quantities are summed for duplicate products.
    - The guest cart is deleted.
    """
    serializer = MergeCartSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    session_id = serializer.validated_data['session_id']
    merged_cart = Cart.merge_guest_into_user(request.user, session_id)

    return Response(CartSerializer(merged_cart).data, status=status.HTTP_200_OK)
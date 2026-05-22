from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from products.models import Product
from .models import UserProfile, WishlistItem
from .serializers import UserProfileSerializer, WishlistItemSerializer


# ──────────────────────────────────────────────────────────────────────────────
# Profile
# ──────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    GET  → Return the authenticated user's profile.
    PUT  → Replace all profile fields.
    PATCH → Update specific profile fields.
    """
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    partial = request.method == 'PATCH'
    serializer = UserProfileSerializer(profile, data=request.data, partial=partial)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


# ──────────────────────────────────────────────────────────────────────────────
# Wishlist
# ──────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def wishlist(request):
    """
    GET  → List all wishlist items for the authenticated user.
    POST → Add a product to the wishlist.
          Body: { "product_id": <int> }
    """
    if request.method == 'GET':
        items = WishlistItem.objects.filter(user=request.user).select_related('product')
        serializer = WishlistItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)

    # POST — add to wishlist
    product_id = request.data.get('product_id')
    if not product_id:
        return Response({'error': 'product_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    product = get_object_or_404(Product, pk=product_id, is_available=True)
    item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)

    if not created:
        return Response(
            {'message': 'Already in wishlist.', 'id': item.id},
            status=status.HTTP_200_OK,
        )

    serializer = WishlistItemSerializer(item, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def wishlist_remove(request, product_id):
    """
    DELETE /api/users/wishlist/<product_id>/ → Remove a product from the wishlist.
    """
    item = get_object_or_404(WishlistItem, user=request.user, product_id=product_id)
    item.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

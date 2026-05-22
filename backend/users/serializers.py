from rest_framework import serializers
from .models import UserProfile, WishlistItem
from products.serializers import ProductSerializer


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'phone',
            'address_line_1',
            'address_line_2',
            'city',
            'state',
            'pincode',
        ]


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'product_id', 'added_at']
        read_only_fields = ['id', 'added_at']

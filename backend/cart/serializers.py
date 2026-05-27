from rest_framework import serializers
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    price = serializers.DecimalField(source='price', max_digits=10, decimal_places=2, read_only=True)
    stock = serializers.IntegerField(source='product.stock', read_only=True)

    class Meta:
        model = CartItem
        fields = [
            'id',
            'product_id',
            'product_name',
            'purchase_option',
            'price',
            'stock',
            'quantity',
            'added_at',
        ]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'id',
            'user',
            'session_id',
            'expires_at',
            'created_at',
            'updated_at',
            'items',
            'item_count',
            'total',
        ]

    def get_item_count(self, obj):
        return sum(item.quantity for item in obj.items.all())

    def get_total(self, obj):
        return sum(
            item.quantity * item.price
            for item in obj.items.all()
            if item.product is not None and item.product.is_available
        )


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    purchase_option = serializers.ChoiceField(choices=['individual', 'set'], default='individual')

    def validate_product_id(self, value):
        from products.models import Product
        try:
            product = Product.objects.get(id=value, is_available=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError('Product not found or unavailable.')
        if product.stock < 1:
            raise serializers.ValidationError('Product is out of stock.')
        return value


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0)


class MergeCartSerializer(serializers.Serializer):
    session_id = serializers.CharField(required=True, allow_blank=False)
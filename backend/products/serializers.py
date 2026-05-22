from rest_framework import serializers
from .models import Product, Review


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    is_verified_buyer = serializers.BooleanField(read_only=True)

    class Meta:
        model = Review
        fields = [
            'id',
            'user',
            'user_name',
            'product',
            'rating',
            'title',
            'comment',
            'created_at',
            'is_verified_buyer',
        ]
        read_only_fields = ['id', 'user', 'product', 'created_at', 'is_verified_buyer']

    def create(self, validated_data):
        # is_verified_buyer is read-only, so we don't need to pass it
        return super().create(validated_data)


class ProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    isNew = serializers.BooleanField(source='is_new', read_only=True)
    avg_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'price',
            'stock',
            'image',
            'image_url',
            'category',
            'is_available',
            'is_new',
            'isNew',
            'created_at',
            'avg_rating',
            'review_count',
        ]

    def get_image_url(self, obj):
        request = self.context.get('request')
        if not obj.image:
            return None
        if request is None:
            return obj.image.url
        return request.build_absolute_uri(obj.image.url)

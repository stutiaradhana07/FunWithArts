from rest_framework import serializers

from .models import Product, ProductQuestion, Review


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


class ProductQuestionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    answered_by_name = serializers.CharField(source='answered_by.username', read_only=True)
    is_answered = serializers.BooleanField(read_only=True)

    class Meta:
        model = ProductQuestion
        fields = [
            'id',
            'product',
            'user',
            'user_name',
            'asker_name',
            'question',
            'answer_text',
            'answered_by',
            'answered_by_name',
            'answered_at',
            'created_at',
            'updated_at',
            'is_answered',
        ]
        read_only_fields = [
            'id',
            'product',
            'user',
            'user_name',
            'answered_by',
            'answered_by_name',
            'answered_at',
            'created_at',
            'updated_at',
            'is_answered',
        ]


class ProductQuestionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductQuestion
        fields = ['answer_text']

    def validate_answer_text(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Answer text cannot be empty.')
        return value


class ProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    image2_url = serializers.SerializerMethodField()
    image3_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    isNew = serializers.BooleanField(source='is_new', read_only=True)
    avg_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    category = serializers.CharField(source='category.name', default='', read_only=True)
    slug = serializers.CharField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'price',
            'stock',
            'image',
            'image_url',
            'image_position',
            'image2',
            'image2_url',
            'image2_position',
            'image3',
            'image3_url',
            'image3_position',
            'video',
            'video_url',
            'has_set_option',
            'set_price',
            'category',
            'is_available',
            'is_new',
            'isNew',
            'created_at',
            'avg_rating',
            'review_count',
        ]

    def _build_absolute_url(self, file_field):
        if not file_field:
            return None
        request = self.context.get('request')
        if request is None:
            return file_field.url
        return request.build_absolute_uri(file_field.url)

    def get_image_url(self, obj):
        return self._build_absolute_url(obj.image)

    def get_image2_url(self, obj):
        return self._build_absolute_url(obj.image2)

    def get_image3_url(self, obj):
        return self._build_absolute_url(obj.image3)

    def get_video_url(self, obj):
        return self._build_absolute_url(obj.video)

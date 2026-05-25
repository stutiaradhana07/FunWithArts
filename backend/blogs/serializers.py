from rest_framework import serializers
from .models import NewsletterSubscriber, Post


class NewsletterSubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscriber
        fields = ['id', 'email', 'created_at']


class NewsletterSubscribeSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the blog feed — excludes full content."""
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'cover_image', 'cover_image_position',
            'excerpt', 'title_is_bold', 'title_is_italic', 'title_font_size',
            'title_color', 'author_name', 'status', 'published_at',
            'created_at', 'updated_at',
        ]

    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.username


class PostDetailSerializer(serializers.ModelSerializer):
    """Full serializer for a single blog post — includes all content."""
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'cover_image', 'cover_image_position',
            'excerpt', 'content', 'title_is_bold', 'title_is_italic',
            'title_font_size', 'title_color', 'author_name', 'status',
            'published_at', 'created_at', 'updated_at',
        ]

    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.username

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
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'cover_image', 'excerpt',
            'author_name', 'status', 'created_at', 'updated_at',
        ]


class PostDetailSerializer(serializers.ModelSerializer):
    """Full serializer for a single blog post — includes all content."""
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'cover_image', 'excerpt',
            'content', 'author_name', 'status', 'created_at', 'updated_at',
        ]

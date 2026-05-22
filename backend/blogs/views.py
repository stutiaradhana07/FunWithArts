from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import NewsletterSubscriber, Post
from .serializers import (
    NewsletterSubscribeSerializer,
    PostListSerializer,
    PostDetailSerializer,
)


@api_view(['POST'])
def newsletter_subscribe(request):
    serializer = NewsletterSubscribeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    subscriber, created = NewsletterSubscriber.objects.get_or_create(
        email=email,
        defaults={'is_active': True},
    )

    if not created and not subscriber.is_active:
        subscriber.is_active = True
        subscriber.save(update_fields=['is_active'])

    return Response(
        {
            'message': 'Subscribed successfully',
            'email': subscriber.email,
            'already_subscribed': not created,
        },
        status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED,
    )


@api_view(['GET'])
def post_list(request):
    """Return all published blog posts (lightweight — no full content)."""
    posts = Post.objects.filter(status='published')
    serializer = PostListSerializer(posts, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def post_detail(request, slug):
    """Return a single published blog post by slug (full content)."""
    post = get_object_or_404(Post, slug=slug, status='published')
    serializer = PostDetailSerializer(post)
    return Response(serializer.data)

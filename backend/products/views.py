from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.throttles import ReviewRateThrottle
from .models import Category, Product, ProductQuestion
from .search import DEFAULT_LIMIT, MIN_QUERY_LENGTH, build_product_queryset, parse_limit
from .serializers import (
    ProductQuestionAnswerSerializer,
    ProductQuestionSerializer,
    ProductSerializer,
    ReviewSerializer,
)


@api_view(['GET'])
def product_list(request):
    category = request.query_params.get('category', '').strip()
    search = request.query_params.get('search', '').strip()
    is_new_param = request.query_params.get('is_new', '').strip().lower()
    is_new = is_new_param in ('true', '1', 'yes') if is_new_param else None

    qs = build_product_queryset(search=search, category=category, is_new=is_new)
    serializer = ProductSerializer(qs, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def product_search(request):
    query = (
        request.query_params.get('q', '').strip()
        or request.query_params.get('search', '').strip()
    )
    if not query:
        return Response(
            {'error': 'Provide a search query via ?q=...'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(query) < MIN_QUERY_LENGTH:
        return Response(
            {'error': f'Search query must be at least {MIN_QUERY_LENGTH} characters.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    category = request.query_params.get('category', '').strip()
    is_new_param = request.query_params.get('is_new', '').strip().lower()
    is_new = is_new_param in ('true', '1', 'yes') if is_new_param else None
    limit = parse_limit(request.query_params.get('limit', DEFAULT_LIMIT))

    qs = build_product_queryset(search=query, category=category, is_new=is_new)[:limit]
    products = list(qs)
    serializer = ProductSerializer(products, many=True, context={'request': request})

    return Response(
        {
            'query': query,
            'count': len(products),
            'results': serializer.data,
        }
    )


@api_view(['GET'])
def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews'),
        ),
        pk=pk,
    )
    serializer = ProductSerializer(product, context={'request': request})
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@throttle_classes([ReviewRateThrottle])
def product_reviews(request, pk):
    product = get_object_or_404(Product, pk=pk, is_available=True)

    if request.method == 'GET':
        reviews = product.reviews.select_related('user').all()
        paginator = PageNumberPagination()
        paginator.page_size = 5
        paginator.page_size_query_param = 'page_size'
        paginator.max_page_size = 20

        page = paginator.paginate_queryset(reviews, request)
        serializer = ReviewSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    if not request.user.is_authenticated:
        return Response(
            {'error': 'Authentication required to leave a review.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if product.reviews.filter(user=request.user).exists():
        return Response(
            {'error': 'You have already reviewed this product.'},
            status=status.HTTP_409_CONFLICT,
        )

    serializer = ReviewSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(user=request.user, product=product)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def product_review_summary(request, pk):
    product = get_object_or_404(Product, pk=pk, is_available=True)
    reviews = product.reviews.all()
    total = reviews.count()

    breakdown = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for review in reviews.values('rating').annotate(count=Count('rating')):
        breakdown[review['rating']] = review['count']

    avg_result = reviews.aggregate(avg=Avg('rating'))
    avg_rating = round(avg_result['avg'], 1) if avg_result['avg'] is not None else None

    return Response(
        {
            'avg_rating': avg_rating,
            'review_count': total,
            'breakdown': breakdown,
        }
    )


@api_view(['GET', 'POST'])
def product_questions(request, pk):
    product = get_object_or_404(Product, pk=pk, is_available=True)

    if request.method == 'GET':
        questions = product.questions.select_related('user', 'answered_by').all()
        serializer = ProductQuestionSerializer(questions, many=True)
        return Response(serializer.data)

    serializer = ProductQuestionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = request.user if request.user.is_authenticated else None
    serializer.save(
        product=product,
        user=user,
        asker_name=serializer.validated_data['asker_name'].strip(),
        question=serializer.validated_data['question'].strip(),
    )
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def product_question_answer(request, pk, question_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return Response(
            {'error': 'Only staff can moderate product questions.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    question = get_object_or_404(
        ProductQuestion.objects.select_related('product'),
        pk=question_id,
        product_id=pk,
    )

    if request.method == 'DELETE':
        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ProductQuestionAnswerSerializer(question, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save(answered_by=request.user, answered_at=timezone.now())

    return Response(ProductQuestionSerializer(question).data)


@api_view(['GET'])
def category_list(request):
    categories = (
        Category.objects.filter(products__is_available=True)
        .distinct()
        .order_by('name')
        .values_list('name', flat=True)
    )
    return Response(list(categories))

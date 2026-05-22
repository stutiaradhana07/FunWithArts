from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from .models import Product
from .search import DEFAULT_LIMIT, MIN_QUERY_LENGTH, build_product_queryset, parse_limit
from .serializers import ProductSerializer, ReviewSerializer


@api_view(['GET'])
def product_list(request):
    """
    GET /api/products/
    Optional query params:
      ?category=Decor   — filter by category (case-insensitive)
      ?search=bowl      — search name + description
      ?is_new=true      — filter to new arrivals only
    """
    category = request.query_params.get('category', '').strip()
    search = request.query_params.get('search', '').strip()
    is_new_param = request.query_params.get('is_new', '').strip().lower()
    is_new = is_new_param in ('true', '1', 'yes') if is_new_param else None

    qs = build_product_queryset(search=search, category=category, is_new=is_new)
    serializer = ProductSerializer(qs, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def product_search(request):
    """
    GET /api/search/?q=bowl
    Optional: category, is_new, limit
    """
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
def product_reviews(request, pk):
    """
    GET  /api/products/<id>/reviews/?page=1&page_size=5 — paginated reviews.
    POST /api/products/<id>/reviews/ — create a review (auth required).
    Body: { "rating": 4, "title": "Loved it!", "comment": "Great product!" }
    """
    product = get_object_or_404(Product, pk=pk, is_available=True)

    if request.method == 'GET':
        reviews = product.reviews.select_related('user').all()

        # Pagination
        try:
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 5))
        except (ValueError, TypeError):
            page = 1
            page_size = 5

        page = max(page, 1)
        page_size = min(max(page_size, 1), 20)  # clamp 1–20

        total = reviews.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = min(page, total_pages)

        start = (page - 1) * page_size
        page_reviews = reviews[start:start + page_size]

        return Response({
            'results': ReviewSerializer(page_reviews, many=True).data,
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': total_pages,
        })

    # POST — requires authentication
    if not request.user.is_authenticated:
        return Response(
            {'error': 'Authentication required to leave a review.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Check for duplicate review
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
    """
    GET /api/products/<id>/reviews/summary/
    Returns: { avg_rating, review_count, breakdown: {1: 0, 2: 3, 3: 5, 4: 12, 5: 8} }
    """
    product = get_object_or_404(Product, pk=pk, is_available=True)
    reviews = product.reviews.all()
    total = reviews.count()

    # Rating distribution
    breakdown = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for review in reviews.values('rating').annotate(count=Count('rating')):
        breakdown[review['rating']] = review['count']

    # Average
    avg_result = reviews.aggregate(avg=Avg('rating'))
    avg_rating = round(avg_result['avg'], 1) if avg_result['avg'] is not None else None

    return Response({
        'avg_rating': avg_rating,
        'review_count': total,
        'breakdown': breakdown,
    })


@api_view(['GET'])
def category_list(request):
    """
    GET /api/products/categories/
    Returns a list of distinct category strings for all available products.
    """
    categories = (
        Product.objects.filter(is_available=True)
        .values_list('category', flat=True)
        .distinct()
        .order_by('category')
    )
    return Response(list(categories))

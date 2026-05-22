from django.db.models import Avg, Count, Q

from .models import Product

MIN_QUERY_LENGTH = 2
DEFAULT_LIMIT = 50
MAX_LIMIT = 100


def build_product_queryset(*, search='', category='', is_new=None):
    qs = Product.objects.filter(is_available=True).annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews'),
    ).order_by('-created_at')

    category = (category or '').strip()
    if category:
        qs = qs.filter(category__iexact=category)

    search = (search or '').strip()
    if search:
        qs = qs.filter(
            Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(category__icontains=search)
        )

    if is_new is True:
        qs = qs.filter(is_new=True)

    return qs


def parse_limit(value):
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return DEFAULT_LIMIT
    return max(1, min(limit, MAX_LIMIT))

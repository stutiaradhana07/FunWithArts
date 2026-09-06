from django.db.models import Avg, Count, Q

from .models import Product

MIN_QUERY_LENGTH = 2
DEFAULT_LIMIT = 50
MAX_LIMIT = 100


from decimal import Decimal, InvalidOperation


def build_product_queryset(*, search='', category='', is_new=None, min_price=None):
    qs = Product.objects.filter(is_available=True).select_related('category').annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews'),
    ).order_by('-created_at')

    category = (category or '').strip()
    if category:
        qs = qs.filter(category__name__iexact=category)

    search = (search or '').strip()
    if search:
        qs = qs.filter(
            Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(category__name__icontains=search)
        )

    if is_new is True:
        qs = qs.filter(is_new=True)

    if min_price is not None:
        try:
            min_p = Decimal(str(min_price))
            qs = qs.filter(price__gte=min_p)
        except (ValueError, TypeError, InvalidOperation):
            pass

    return qs


def parse_limit(value):
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return DEFAULT_LIMIT
    return max(1, min(limit, MAX_LIMIT))

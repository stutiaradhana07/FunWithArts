from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from blogs.views import newsletter_subscribe
from orders.views import delivery_check
from products.views import product_search


@api_view(['GET'])
def health_check(request):
    return Response({'status': 'ok'})


urlpatterns = [
    path('admin/', admin.site.urls),

    # ── API routes (v1) ────────────────────────────────────────────────────
    path('api/health/', health_check),
    path('api/products/', include('products.urls')),
    path('api/search/', product_search),
    path('api/workshops/', include('workshops.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/delivery-check/', delivery_check),
    path('api/auth/', include('accounts.urls')),
    path('api/blogs/', include('blogs.urls')),
    path('api/newsletter/subscribe/', newsletter_subscribe),
    path('api/users/', include('users.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/cart/', include('cart.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.urls import path
from .views import guest_order_lookup, order_list_create, order_detail

urlpatterns = [
    path('', order_list_create),                # GET (paginated/filterable) + POST create
    path('lookup/', guest_order_lookup),        # GET guest order lookup (no auth)
    path('<int:pk>/', order_detail),            # GET specific order
]

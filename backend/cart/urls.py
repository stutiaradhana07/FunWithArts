from django.urls import path
from .views import (
    cart_add_item,
    cart_clear,
    cart_detail,
    cart_merge,
    cart_remove_item,
    cart_update_item,
)

urlpatterns = [
    path('', cart_detail),                          # GET  — view cart
    path('add/', cart_add_item),                    # POST — add item
    path('items/<int:item_id>/', cart_update_item), # PATCH  — update qty
    path('items/<int:item_id>/delete/', cart_remove_item),  # DELETE — remove item
    path('clear/', cart_clear),                     # POST  — clear cart
    path('merge/', cart_merge),                     # POST  — merge guest → user (auth required)
]
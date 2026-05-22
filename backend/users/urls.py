from django.urls import path
from .views import user_profile, wishlist, wishlist_remove

urlpatterns = [
    path('profile/', user_profile),
    path('wishlist/', wishlist),
    path('wishlist/<int:product_id>/', wishlist_remove),
]

from django.urls import path
from .views import newsletter_subscribe, post_list, post_detail

urlpatterns = [
    path('subscribe/', newsletter_subscribe),
    path('', post_list, name='blog-post-list'),
    path('<slug:slug>/', post_detail, name='blog-post-detail'),
]

from django.urls import path
from .views import exchange_list_create, exchange_detail

urlpatterns = [
    path('', exchange_list_create),       # GET (list) + POST (create)
    path('<int:pk>/', exchange_detail),   # GET specific exchange status
]

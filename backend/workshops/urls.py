from django.urls import path
from .views import workshop_list, workshop_detail, create_booking

urlpatterns = [
    path('', workshop_list),
    path('<int:pk>/', workshop_detail),
    path('book/', create_booking),
]

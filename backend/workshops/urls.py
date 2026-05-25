from django.urls import path
from .views import (
    workshop_list,
    workshop_detail,
    initiate_workshop_payment,
    verify_workshop_payment,
    workshop_razorpay_webhook,
    my_bookings,
)

urlpatterns = [
    path('', workshop_list),
    path('<int:pk>/', workshop_detail),
    path('bookings/', my_bookings),
    path('initiate-payment/', initiate_workshop_payment),
    path('payment/verify/', verify_workshop_payment),
    path('payment/webhook/', workshop_razorpay_webhook),
]

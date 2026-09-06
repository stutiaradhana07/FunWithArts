from django.urls import path
from .views import (
    exchange_list_create,
    exchange_detail,
    exchange_create_payment_order,
    exchange_verify_payment,
)

urlpatterns = [
    path('', exchange_list_create, name='exchange-list-create'),       # GET (list) + POST (create)
    path('<int:pk>/', exchange_detail, name='exchange-detail'),        # GET specific exchange status
    path('<int:pk>/create-payment-order/', exchange_create_payment_order, name='exchange-create-payment-order'),
    path('<int:pk>/verify-payment/', exchange_verify_payment, name='exchange-verify-payment'),
]

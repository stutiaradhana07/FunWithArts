from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment creation and verification
    path('create-order/', views.create_payment_order, name='create_payment_order'),
    path('verify/', views.verify_payment, name='verify_payment'),
    path('<int:payment_id>/', views.payment_detail, name='payment_detail'),
    
    # Refunds
    path('refund/', views.create_refund, name='create_refund'),
    
    # Webhook
    path('webhook/', views.razorpay_webhook, name='razorpay_webhook'),
]

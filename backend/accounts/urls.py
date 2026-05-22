from django.urls import path
from .views import (
    current_user,
    google_login,
    login_user,
    logout_user,
    password_reset,
    password_reset_confirm,
    register_user,
)

urlpatterns = [
    path('register/', register_user),
    path('login/', login_user),
    path('google/', google_login),
    path('logout/', logout_user),
    path('me/', current_user),
    path('password_reset/', password_reset),
    path('password_reset_confirm/', password_reset_confirm),
]

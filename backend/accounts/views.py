from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string

from notifications.emails import send_email_async

from .serializers import (
    GoogleLoginSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    RegisterSerializer,
)


@api_view(['POST'])
def register_user(request):
    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        login(request, user)
        return Response(
            {
                'message': 'User created successfully',
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                },
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login_user(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data['username']
    password = serializer.validated_data['password']

    user = authenticate(username=username, password=password)

    if user:
        token, _ = Token.objects.get_or_create(user=user)
        login(request, user)
        return Response(
            {
                'message': 'Login successful',
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                },
            }
        )

    return Response(
        {'error': 'Invalid credentials'},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """Delete the user's auth token, effectively logging them out."""
    try:
        request.user.auth_token.delete()
    except Token.DoesNotExist:
        pass
    return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    user = request.user
    return Response(
        {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        }
    )


# ──────────────────────────────────────────────────────────────────────
# Password Reset Flow
# ──────────────────────────────────────────────────────────────────────

_token_generator = PasswordResetTokenGenerator()


@api_view(['POST'])
def password_reset(request):
    """
    POST /api/auth/password_reset/
    Accepts { "email": "user@example.com" }

    Always returns a generic success message to prevent email enumeration.
    If the user exists, generates a one-time token and emails a reset link
    pointing to the React frontend.
    """
    serializer = PasswordResetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']

    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        pass  # Don't leak whether the account exists
    else:
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = _token_generator.make_token(user)

        reset_url = (
            f'{settings.FRONTEND_URL}/reset-password/'
            f'?uid={uidb64}&token={token}'
        )

        context = {
            'user': user,
            'reset_url': reset_url,
            'studio_name': 'Udaan Studio',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        }

        subject = 'Reset your Udaan Studio password'
        body_plain = render_to_string('notifications/password_reset.txt', context)
        body_html = render_to_string('notifications/password_reset.html', context)

        send_email_async(subject, body_plain, body_html, [user.email])

    # Always return the same message regardless of whether the user exists
    return Response(
        {
            'message': (
                'If an account with that email exists, '
                'we have sent a password reset link.'
            ),
        }
    )


@api_view(['POST'])
def password_reset_confirm(request):
    """
    POST /api/auth/password_reset_confirm/
    Accepts { "uidb64": "...", "token": "...", "new_password": "..." }

    Validates the uid+token pair, then sets the new password.
    The token is consumed (one-time use — Django's default behaviour).
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({'message': 'Password has been reset successfully.'})


# ──────────────────────────────────────────────────────────────────────
# Google OAuth2 Login
# ──────────────────────────────────────────────────────────────────────

@api_view(['POST'])
def google_login(request):
    """
    POST /api/auth/google/
    Accepts { "id_token": "..." } from the frontend Google Sign-In SDK.

    Verifies the id_token with Google, gets/creates the user, and returns
    a DRF Token so the frontend can use Token Authentication for subsequent
    API calls.
    """
    serializer = GoogleLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    id_info = serializer.validated_data['id_token']
    user = serializer.get_or_create_user(id_info)

    token, _ = Token.objects.get_or_create(user=user)
    login(request, user)

    return Response(
        {
            'message': 'Google login successful',
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
        },
        status=status.HTTP_200_OK,
    )

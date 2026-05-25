from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from notifications.emails import send_email_async

from .serializers import (
    CurrentUserSerializer,
    GoogleLoginSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    RegisterSerializer,
)
from .throttles import LoginRateThrottle, PasswordResetRateThrottle, RegisterRateThrottle


def _user_payload(user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    }


@api_view(['POST'])
@throttle_classes([RegisterRateThrottle])
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
                'user': _user_payload(user),
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@throttle_classes([LoginRateThrottle])
def login_user(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username_or_email = serializer.validated_data['username']
    password = serializer.validated_data['password']

    user = authenticate(username=username_or_email, password=password)
    if not user:
        try:
            user_obj = User.objects.get(email__iexact=username_or_email)
            user = authenticate(username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

    if user:
        token, _ = Token.objects.get_or_create(user=user)
        login(request, user)
        return Response(
            {
                'message': 'Login successful',
                'token': token.key,
                'user': _user_payload(user),
            }
        )

    return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    try:
        request.user.auth_token.delete()
    except Token.DoesNotExist:
        pass
    return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def current_user(request):
    user = request.user
    if request.method == 'GET':
        return Response(CurrentUserSerializer(user).data)

    serializer = CurrentUserSerializer(user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


_token_generator = PasswordResetTokenGenerator()


@api_view(['POST'])
@throttle_classes([PasswordResetRateThrottle])
def password_reset(request):
    serializer = PasswordResetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']

    try:
        user = User.objects.get(email__iexact=email)
    except (User.DoesNotExist, User.MultipleObjectsReturned):
        pass
    else:
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = _token_generator.make_token(user)

        reset_url = f'{settings.FRONTEND_URL}/reset-password/?uid={uidb64}&token={token}'
        context = {
            'user': user,
            'reset_url': reset_url,
            'studio_name': 'Fun with Art',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        }

        subject = 'Reset your Fun with Art password'
        body_plain = render_to_string('notifications/password_reset.txt', context)
        body_html = render_to_string('notifications/password_reset.html', context)
        send_email_async(subject, body_plain, body_html, [user.email])

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
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({'message': 'Password has been reset successfully.'})


@api_view(['POST'])
def google_login(request):
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
            'user': _user_payload(user),
        },
        status=status.HTTP_200_OK,
    )

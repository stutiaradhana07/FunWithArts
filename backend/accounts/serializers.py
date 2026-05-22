from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import serializers


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'email': {'required': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class PasswordResetSerializer(serializers.Serializer):
    """Accepts an email address and (behind the scenes) generates a reset token."""
    email = serializers.EmailField()

    def validate_email(self, value):
        # Normalize to lowercase for consistent lookups.
        return value.lower().strip()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Validates the uid + token, then sets the new password."""
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8, write_only=True)

    _token_generator = PasswordResetTokenGenerator()

    def validate(self, attrs):
        from django.utils.http import urlsafe_base64_decode
        from django.utils.encoding import force_str

        uidb64 = attrs['uidb64']
        token = attrs['token']

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({'uidb64': 'Invalid or expired reset link.'})

        if not self._token_generator.check_token(user, token):
            raise serializers.ValidationError({'token': 'Invalid or expired reset token.'})

        attrs['user'] = user
        return attrs

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class GoogleLoginSerializer(serializers.Serializer):
    """
    Accepts a Google `id_token` from the frontend Google Sign-In SDK.

    The backend verifies the token using Google's public certs, extracts
    the user's email & name, and creates or retrieves a Django User.
    """
    id_token = serializers.CharField()

    def validate_id_token(self, value):
        try:
            from google.oauth2 import id_token as google_id_token
            from google.auth.transport import requests as google_requests
        except ImportError:
            raise serializers.ValidationError(
                'Google authentication is not configured on the server.'
            )

        try:
            id_info = google_id_token.verify_oauth2_token(
                value,
                google_requests.Request(),
                audience=None,  # Allow any audience; validate below
            )
        except ValueError as exc:
            raise serializers.ValidationError(f'Invalid Google token: {exc}')

        # Validate audience against our configured client ID
        from django.conf import settings
        expected_audience = settings.GOOGLE_CLIENT_ID
        if expected_audience and id_info.get('aud') != expected_audience:
            raise serializers.ValidationError('Token audience mismatch.')

        if not id_info.get('email_verified', False):
            raise serializers.ValidationError('Google email not verified.')

        return id_info

    def get_or_create_user(self, id_info):
        """Get existing user or create a new one from verified Google token info."""
        from django.contrib.auth.models import User

        email = id_info['email']
        google_id = id_info.get('sub', '')

        user = User.objects.filter(email__iexact=email).first()

        if user is None:
            # Build a unique username from the email prefix + Google sub
            base_username = email.split('@')[0]
            username = base_username
            suffix = 1
            while User.objects.filter(username=username).exists():
                username = f'{base_username}{suffix}'
                suffix += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=id_info.get('given_name', ''),
                last_name=id_info.get('family_name', ''),
            )
            # Set unusable password so email+password login is blocked
            user.set_unusable_password()
            user.save()

        return user

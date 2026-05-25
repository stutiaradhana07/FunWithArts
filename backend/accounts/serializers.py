from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='An account with this email already exists.',
            )
        ],
    )
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(help_text='Username or email address')
    password = serializers.CharField(write_only=True)

    def validate_username(self, value):
        return value.lower().strip()


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower().strip()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8, write_only=True)

    _token_generator = PasswordResetTokenGenerator()

    def validate(self, attrs):
        from django.utils.encoding import force_str
        from django.utils.http import urlsafe_base64_decode

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
    id_token = serializers.CharField()

    def validate_id_token(self, value):
        try:
            from google.auth.transport import requests as google_requests
            from google.oauth2 import id_token as google_id_token
        except ImportError:
            raise serializers.ValidationError(
                'Google authentication is not configured on the server.'
            )

        try:
            id_info = google_id_token.verify_oauth2_token(
                value,
                google_requests.Request(),
                audience=None,
            )
        except ValueError as exc:
            raise serializers.ValidationError(f'Invalid Google token: {exc}')

        from django.conf import settings

        expected_audience = settings.GOOGLE_CLIENT_ID
        if expected_audience and id_info.get('aud') != expected_audience:
            raise serializers.ValidationError('Token audience mismatch.')

        if not id_info.get('email_verified', False):
            raise serializers.ValidationError('Google email not verified.')

        return id_info

    def get_or_create_user(self, id_info):
        email = id_info['email']
        user = User.objects.filter(email__iexact=email).first()

        if user is None:
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
            user.set_unusable_password()
            user.save()

        return user


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'is_superuser']
        read_only_fields = ['id', 'email', 'is_staff', 'is_superuser']

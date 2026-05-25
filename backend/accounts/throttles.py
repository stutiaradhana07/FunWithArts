"""
Custom throttle classes targeting sensitive authentication endpoints.

Uses DRF's AnonRateThrottle under the hood — each subclass declares its own
'scope' so the rate can be configured independently in settings.py.
"""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'


class RegisterRateThrottle(AnonRateThrottle):
    scope = 'register'


class PasswordResetRateThrottle(AnonRateThrottle):
    scope = 'password_reset'


class ReviewRateThrottle(UserRateThrottle):
    """
    Rate limit on product reviews to prevent spam.
    Scope: 'review_post' — rate can be configured in settings.REST_FRAMEWORK
    Example: 'REST_FRAMEWORK = {'DEFAULT_THROTTLE_RATES': {'review_post': '5/day'}}'
    """
    scope = 'review_post'
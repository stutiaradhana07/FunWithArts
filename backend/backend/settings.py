"""
Django settings for backend project.
"""
import os
import sys
from pathlib import Path
import dj_database_url
from django.core.exceptions import ImproperlyConfigured

# ---------- dotenv (local dev only) ----------
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SECURITY ---
DEBUG = os.getenv('DJANGO_DEBUG', os.getenv('DEBUG', 'false')).lower() == 'true'

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'insecure-debug-key-do-not-use-in-production'
    else:
        raise ImproperlyConfigured('DJANGO_SECRET_KEY environment variable is required in production.')

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")).split(",")
_railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
if _railway_domain:
    ALLOWED_HOSTS.append(_railway_domain)
    ALLOWED_HOSTS.append(f".{_railway_domain}")

# --- APPS ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'users',
    'products',
    'workshops',
    'orders',
    'blogs',
    'accounts',
    'payments',
    'cart',
    'notifications',
]

# --- MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'backend.cors.SimpleCORSMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'notifications' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# --- DATABASE CONFIGURATION ---
# dj-database-url >= 2.x changed its API: conn_max_age / conn_health_checks
# must NOT be passed to config() — they go to parse() instead.
# We also guard against a truthy-but-incomplete dict (NAME='') which Django
# would reject with ImproperlyConfigured.
_db_url = (
    os.environ.get('DATABASE_URL')
    or os.environ.get('DATABASE_PRIVATE_URL')  # Railway private network URL
    or os.environ.get('POSTGRES_URL')
)

if _db_url:
    database_config = dj_database_url.parse(
        _db_url,
        conn_max_age=600,
        conn_health_checks=True,
    )
else:
    database_config = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

# Safety net: if parse() returned a dict without a usable NAME, fall back
if not database_config.get('NAME'):
    database_config = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

DATABASES = {'default': database_config}

# --- TEST DATABASE OVERRIDE ---
# Always use SQLite for local tests. Railway's internal PostgreSQL URL
# (funwitharts.railway.internal) is unreachable from outside Railway's network,
# so running tests via `railway run` would fail. Forcing SQLite avoids this.
if 'test' in sys.argv or os.environ.get('DJANGO_TEST'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'test_db.sqlite3',
        }
    }

# --- AUTHENTICATION & PASSWORDS ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- INTERNATIONALIZATION ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# --- STATIC & MEDIA FILES ---
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --- CORS ---
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        'DJANGO_CORS_ALLOWED_ORIGINS',
        os.getenv(
            'CORS_ALLOWED_ORIGINS',
            'http://127.0.0.1:5173,http://localhost:5173',
        ),
    ).split(',')
    if origin.strip()
]

# --- CSRF ---
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        'DJANGO_CSRF_TRUSTED_ORIGINS',
        os.getenv(
            'CSRF_TRUSTED_ORIGINS',
            'http://127.0.0.1:5173,http://localhost:5173',
        ),
    ).split(',')
    if origin.strip()
]

if _railway_domain:
    CSRF_TRUSTED_ORIGINS.append(f"https://{_railway_domain}")
    CSRF_TRUSTED_ORIGINS.append(f"http://{_railway_domain}")

# Hardcode the known production domain as a fallback
CSRF_TRUSTED_ORIGINS.append("https://funwitharts-production.up.railway.app")


# --- REST FRAMEWORK ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'COERCE_DECIMAL_TO_STRING': False,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'login': '5/minute',
        'register': '5/minute',
        'password_reset': '3/minute',
        'review_post': '5/day',
    },
}

if 'test' in sys.argv or os.environ.get('DJANGO_TEST'):
    REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []

# --- EXTERNAL SERVICES (Razorpay, Email, Google) ---
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', 'rzp_test_StI82O7Jm3heNM')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', 'JumGS1K0sp0CmSLBkXo9suHV')
RAZORPAY_WEBHOOK_SECRET = os.getenv('RAZORPAY_WEBHOOK_SECRET', '')

# Defaulting to console for now as requested
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'false').lower() == 'true'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Fun with Art <hello@funwithart.com>')
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '10'))

FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')

# --- CLOUDINARY ---
CLOUDINARY_URL = os.getenv('CLOUDINARY_URL', 'cloudinary://116638983442739:e8-k5e_wBQbFZulkSnBsbcSrKgc@drclxydp1')
if CLOUDINARY_URL:
    if 'cloudinary' not in INSTALLED_APPS:
        INSTALLED_APPS.append('cloudinary')
    if 'cloudinary_storage' not in INSTALLED_APPS:
        INSTALLED_APPS.append('cloudinary_storage')
    # Django 4.2+ replaced DEFAULT_FILE_STORAGE with the STORAGES dict.
    # Set both for maximum compatibility.
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    STORAGES = {
        'default': {'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage'},
        'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
    }
    # Parse CLOUDINARY_URL into the CLOUDINARY_STORAGE dict that
    # django-cloudinary-storage expects, and also initialize the cloudinary SDK.
    try:
        import urllib.parse as _urlparse
        _cld = _urlparse.urlparse(CLOUDINARY_URL)
        CLOUDINARY_STORAGE = {
            'CLOUD_NAME': _cld.hostname,
            'API_KEY': _cld.username,
            'API_SECRET': _cld.password,
        }
        # Set the env var so the cloudinary SDK picks up credentials.
        os.environ.setdefault('CLOUDINARY_URL', CLOUDINARY_URL)
        import cloudinary
        cloudinary.config(
            cloud_name=_cld.hostname,
            api_key=_cld.username,
            api_secret=_cld.password,
            secure=True,
        )
    except Exception:
        pass

# --- PRODUCTION SECURITY ---
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# --- FIX FOR LOG WARNINGS ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- TINYMCE CONFIGURATION ---
TINYMCE_API_KEY = os.getenv('TINYMCE_API_KEY', 'no-api-key')
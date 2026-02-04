# settings.py

from pathlib import Path
import os
from datetime import timedelta

import cloudinary
import dj_database_url
from decouple import config, Csv

# --------------------------------------------------
# Base
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------
# Security
# --------------------------------------------------
SECRET_KEY = "django-insecure-w-d!supz(a#gjuw^y0iw_8)itsdb^j53ld@%5_!fspo9_5t9i3"

DEBUG = config("DEBUG", cast=bool, default=False)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    cast=Csv(),
    default="localhost,127.0.0.1"
)

CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    cast=Csv(),
    default=""
)

SITE_URL = config("SITE_URL", default="http://localhost:8000")

# --------------------------------------------------
# HTTPS / Proxy (Railway)
# --------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = "Lax"

# --------------------------------------------------
# Installed Apps
# --------------------------------------------------
INSTALLED_APPS = [
    "jazzmin",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "corsheaders",
    "rest_framework",

    # Local apps
    "accounts",
    "students",
    "teachers",
    "announcements",
    "core",
    "results",
    "OAuthForm",
    "landingpage",
]

# --------------------------------------------------
# Middleware
# --------------------------------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# --------------------------------------------------
# URLs / WSGI
# --------------------------------------------------
ROOT_URLCONF = "paranga_sms.urls"
WSGI_APPLICATION = "paranga_sms.wsgi.application"

# --------------------------------------------------
# Templates
# --------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates", BASE_DIR / "layout"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --------------------------------------------------
# Database (Railway)
# --------------------------------------------------
DATABASES = {
    "default": dj_database_url.parse(
        config("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True,
    )
}

# --------------------------------------------------
# Authentication
# --------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --------------------------------------------------
# Internationalization
# --------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Dar_es_Salaam"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------
# Static / Media
# --------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --------------------------------------------------
# CORS
# --------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://parangasec.online",
    "https://www.parangasec.online",
]

# --------------------------------------------------
# Django REST Framework
# --------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
}

# --------------------------------------------------
# JWT
# --------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# --------------------------------------------------
# Cloudinary
# --------------------------------------------------
CLOUDINARY_CLOUD_NAME = config("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = config("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = config("CLOUDINARY_API_SECRET")

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
)

DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

# --------------------------------------------------
# Africa’s Talking (CRASH-PROOF)
# --------------------------------------------------
AFRICASTALKING_USERNAME = config("AFRICASTALKING_USERNAME", default="")
AFRICASTALKING_API_KEY = config("AFRICASTALKING_API_KEY", default="")
AFRICASTALKING_SENDER_ID = config("AFRICASTALKING_SENDER_ID", default="")

# --------------------------------------------------
# Email (SendGrid)
# --------------------------------------------------
EMAIL_BACKEND = "paranga_sms.sendgrid_backend.SendGridAPIEmailBackend"
SENDGRID_API_KEY = config("SENDGRID_API_KEY")
DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL",
    default="Paranga Secondary <no-reply@parangasec.online>"
)

# --------------------------------------------------
# Login redirects
# --------------------------------------------------
LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/admin/"
LOGOUT_REDIRECT_URL = "/admin/login/"

# --------------------------------------------------
# Default PK
# --------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

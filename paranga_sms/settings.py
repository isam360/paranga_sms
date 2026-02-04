from pathlib import Path
import os
import cloudinary
from decouple import config, Csv
import dj_database_url
from datetime import timedelta

# --------------------------------------------------------------
# Paths & Base
# --------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------
# Security
# --------------------------------------------------------------
SECRET_KEY = config("SECRET_KEY", default="django-insecure-default-secret-key")
DEBUG = config("DEBUG", cast=bool, default=True)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    cast=Csv(),
    default="localhost,127.0.0.1,parangasec.up.railway.app,parangasec.online,www.parangasec.online"
)

CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    cast=Csv(),
    default="https://parangasec.up.railway.app,http://localhost:8000,http://127.0.0.1:8000"
)

SITE_URL = config("SITE_URL", default="https://parangasec.online")

# --------------------------------------------------------------
# Security Settings for Railway Deployment (HTTPS, CSRF, Cookies)
# --------------------------------------------------------------
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_METHODS = ["GET", "POST", "OPTIONS", "PUT", "DELETE"]
CORS_ALLOW_HEADERS = [
    "Content-Type",
    "X-CSRFToken",
    "Authorization",
    "Access-Control-Allow-Origin",
]

# --------------------------------------------------------------
# Installed Apps
# --------------------------------------------------------------
INSTALLED_APPS = [
    # Admin / UI
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 3rd Party
    'corsheaders',
    'rest_framework',
    # 'rest_framework.authtoken',
    # 'rest_framework_simplejwt.token_blacklist',

    # Local Apps
    'accounts',
    'students',
    'teachers',
    'announcements',
    'core',
    'results',
    'OAuthForm',
    'landingpage',
]

# --------------------------------------------------------------
# Cloudinary config (with defaults)
# --------------------------------------------------------------
CLOUDINARY_CLOUD_NAME = config("CLOUDINARY_CLOUD_NAME", default="dsntkh10i")
CLOUDINARY_API_KEY = config("CLOUDINARY_API_KEY", default="761499212215921")
CLOUDINARY_API_SECRET = config("CLOUDINARY_API_SECRET", default="9Q6Pn0r0KEw3t6L2rOReFsl0f4A")

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
)

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
    'API_KEY': CLOUDINARY_API_KEY,
    'API_SECRET': CLOUDINARY_API_SECRET,
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# --------------------------------------------------------------
# Middleware
# --------------------------------------------------------------
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

# --------------------------------------------------------------
# URL Config & WSGI
# --------------------------------------------------------------
ROOT_URLCONF = 'paranga_sms.urls'
WSGI_APPLICATION = 'paranga_sms.wsgi.application'

# --------------------------------------------------------------
# Templates
# --------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'layout', BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# --------------------------------------------------------------
# Database
# --------------------------------------------------------------
# --------------------------------------------------------------
# Database
# --------------------------------------------------------------
import socket

# Function to check if we are running locally
def is_localhost():
    try:
        # Attempt to connect to localhost PostgreSQL
        s = socket.create_connection(("127.0.0.1", 5432), timeout=1)
        s.close()
        return True
    except OSError:
        return False

# Get the DATABASE_URL from environment, otherwise fallback to local dev
DATABASE_URL = config(
    "DATABASE_URL",
    default="postgresql://postgres:BBUPHWcPiGkCioVCqLBVBZJYtaJurmhJ@maglev.proxy.rlwy.net:18652/railway"
)

# Decide SSL based on environment
DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        ssl_require=not is_localhost()  # ✅ SSL required only in production
    )
}

# Optional: Print database info for debugging (remove in production)
if DEBUG:
    print("Using database:", DATABASES["default"]["NAME"])
    print("SSL required:", DATABASES["default"].get("OPTIONS", {}).get("sslmode", "not set"))


# --------------------------------------------------------------
# Authentication
# --------------------------------------------------------------
AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --------------------------------------------------------------
# Internationalization
# --------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Dar_es_Salaam'
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------
# Static and Media Files
# --------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

if DEBUG:
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
else:
    STATICFILES_DIRS = []

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --------------------------------------------------------------
# Django REST Framework
# --------------------------------------------------------------
REST_USE_JWT = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/minute',
        'user': '1000/day',
    },
}

# --------------------------------------------------------------
# Simple JWT
# --------------------------------------------------------------
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
}

# --------------------------------------------------------------
# Africa's Talking SMS API (with defaults)
# --------------------------------------------------------------
AFRICASTALKING_USERNAME = config("AFRICASTALKING_USERNAME", default="dispute_app")
AFRICASTALKING_API_KEY = config("AFRICASTALKING_API_KEY", default="atsk_default_api_key")
AFRICASTALKING_SENDER_ID = config("AFRICASTALKING_SENDER_ID", default="PARANGASEC")

# --------------------------------------------------------------
# Jazzmin Admin Configuration
# --------------------------------------------------------------
JAZZMIN_SETTINGS = {
    "site_title": "Paranga Secondary School | (AIMS)",
    "site_header": "Paranga Secondary School",
    "site_brand": "(AIMS)",
    "welcome_sign": "Academic Information Management System (AIMS)",
    "copyright": "© 2025 Paranga Secondary School",
    # "site_logo": "images/school_logo.jpg",
    # "login_logo": "images/school_logo.jpg",
    # "logout_logo": "images/school_logo.jpg",
    "site_icon": "images/school_logo.jpg",
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": ["auth", "sessions"],
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "search_model": "students.Student",
    "topmenu_links": [
        {"name": "Dashboard", "url": "/admin", "permissions": ["auth.view_user"]},
        {"model": "students.Student"},
        {"model": "teachers.Teacher"},
        {"model": "announcements.Announcement"},
        {"model": "announcements.DisciplinaryMessage"},
        {"name": "School Website", "url": "", "new_window": True},
    ],
    "icons": {
        "auth": "fas fa-users-cog",
        "students.Student": "fas fa-user-graduate",
        "teachers.Teacher": "fas fa-chalkboard-teacher",
        "announcements.Announcement": "fas fa-bullhorn",
        "announcements.DisciplinaryMessage": "fas fa-exclamation-triangle",
    },
    "custom_css": "css/custom_login.css",
    "changeform_format": "horizontal_tabs",
    "related_modal_active": True,
}

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "dark_mode_theme": "darkly",
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
}

# --------------------------------------------------------------
# Default Primary Key Field Type
# --------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --------------------------------------------------------------
# Logging
# --------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'django': {
        'handlers': ['console'],
        'level': 'INFO',
        'propagate': True,
    },
    'loggers': {
        'paranga_sms.sendgrid_backend': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}

# --------------------------------------------------------------
# Authentication Redirects
# --------------------------------------------------------------
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/admin/login/'
PASSWORD_RESET_TIMEOUT_DAYS = 1

# --------------------------------------------------------------
# Email settings (SendGrid)
# --------------------------------------------------------------
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="paranga_sms.sendgrid_backend.SendGridAPIEmailBackend"
)
DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL",
    default="Paranga Secondary <no-reply@parangasec.online>"
)

DOMAIN = config("DOMAIN", default="parangasec.online")
USE_HTTPS = config("USE_HTTPS", cast=bool, default=True)

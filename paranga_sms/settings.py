# settings.py

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
# --------------------------------------------------
SECRET_KEY = config("SECRET_KEY")

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

# --------------------------------------------------------------
# Security Settings for Railway Deployment (HTTPS, CSRF, Cookies)
# --------------------------------------------------------------

# Ensure CSRF cookie is only sent over HTTPS
CSRF_COOKIE_SECURE = True

# Ensure session cookie is only sent over HTTPS
SESSION_COOKIE_SECURE = True

# Set SameSite policy for CSRF cookie to allow login redirects
CSRF_COOKIE_SAMESITE = 'Lax'  # or 'Strict' for tighter security, but may break some logins

# Tell Django it is behind a proxy that handles HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


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
     "results",
    "OAuthForm",
    "landingpage",
]

# Base URL of your site (used in emails, links, etc.)
SITE_URL = "https://parangasec.online"  # or your actual domain in production



# ----------------------------
# Cloudinary config - hardcoded credentials
# ----------------------------
CLOUDINARY_CLOUD_NAME = 'dsntkh10i'
CLOUDINARY_API_KEY = '761499212215921'
CLOUDINARY_API_SECRET = '9Q6Pn0r0KEw3t6L2rOReFsl0f4A'

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
        'DIRS': [BASE_DIR / 'layout', BASE_DIR / 'templates'],  # ✅ Fix here
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
# import socket
# import dj_database_url


# def is_online(host="metro.proxy.rlwy.net", port=5432, timeout=2):
#     try:
#         socket.setdefaulttimeout(timeout)
#         socket.socket().connect((host, port))
#         return True
#     except socket.error:
#         return False

# if is_online():
#     # Use Railway (online PostgreSQL)
#     DATABASE_URL = os.getenv(
#         'DATABASE_URL',
#         'postgresql://postgres:QfEkirSQjJhxDlvIlZsnxlcZvEBUAyos@metro.proxy.rlwy.net:16448/railway'
#     )
#     DATABASES = {
#         'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
#     }
# else:
#     # Use SQLite (offline)
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': BASE_DIR / 'db.sqlite3',
#         }
#     }



DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:BBUPHWcPiGkCioVCqLBVBZJYtaJurmhJ@maglev.proxy.rlwy.net:18652/railway'
    
)

DATABASES = {
    'default': dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        ssl_require=True  # Railway needs SSL
    )
}

# --------------------------------------------------------------
# Authentication
# --------------------------------------------------------------
AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Password validation
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
    # 'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
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
# Africa's Talking SMS API
# --------------------------------------------------------------
AFRICASTALKING_USERNAME = config("AFRICASTALKING_USERNAME")
AFRICASTALKING_API_KEY = config("AFRICASTALKING_API_KEY")
AFRICASTALKING_SENDER_ID = config("AFRICASTALKING_SENDER_ID")

# --------------------------------------------------------------
# Jazzmin Admin Configuration
# --------------------------------------------------------------
JAZZMIN_SETTINGS = {
    "site_title": "Paranga Secondary School | (AIMS)",
    "site_header": "Paranga Secondary School",
    "site_brand": "(AIMS)",
    "welcome_sign": "Academic Information Management System (AIMS)",
    "copyright": "© 2025 Paranga Secondary School",
    
    # Logos
    "site_logo": "images/school_logo.jpg",
    "login_logo": "images/school_logo.jpg",
    "logout_logo": "images/school_logo.jpg",
    "site_icon": "images/school_logo.jpg",  # Optional: Add a favicon

    # Sidebar + Layout
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": ["auth", "sessions"],

    # FontAwesome icons
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    # Search bar model
    "search_model": "students.Student",

    # Top menu shortcuts
    "topmenu_links": [
        {"name": "Dashboard", "url": "/admin", "permissions": ["auth.view_user"]},
        {"model": "students.Student"},
        {"model": "teachers.Teacher"},
        {"model": "announcements.Announcement"},
        {"model": "announcements.DisciplinaryMessage"},
        {"name": "School Website", "url": "", "new_window": True},
    ],

    # Model Icons
    "icons": {
        "auth": "fas fa-users-cog",
        "students.Student": "fas fa-user-graduate",
        "teachers.Teacher": "fas fa-chalkboard-teacher",
        "announcements.Announcement": "fas fa-bullhorn",
        "announcements.DisciplinaryMessage": "fas fa-exclamation-triangle",
    },

    # Custom Login/Logout/Login Error Styling
    "custom_css": "css/custom_login.css",  # 💡 Make sure this file exists in your static folder

    # Customizing actions
    "changeform_format": "horizontal_tabs",  # or "collapsible", "single"
    "related_modal_active": True,
}


JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",               # ✅ Light, clean
    "dark_mode_theme": "darkly",  # ✅ Soft dark
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

# Redirect users to admin login by default
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'  # after login
LOGOUT_REDIRECT_URL = '/admin/login/'

# settings.py
PASSWORD_RESET_TIMEOUT_DAYS = 1  # Optional: link expires in 1 day


# --------------------------------------------------------------
# Email settings (for sending verification emails or other emails)
# --------------------------------------------------------------



# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'            
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'parangasecondary@gmail.com'
# EMAIL_HOST_PASSWORD = 'wyjertciefqjtktb'  
# DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


EMAIL_BACKEND = "paranga_sms.sendgrid_backend.SendGridAPIEmailBackend"
DEFAULT_FROM_EMAIL = "Paranga Secondary <no-reply@parangasec.online>"

# Use your production domain for password reset links
# Django 5.2+ uses this for password reset emails if sites framework is not used
DOMAIN = "parangasec.online"
USE_HTTPS = True


import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
import logging

# Load environment variables from .env file
load_dotenv()

# =====================================================
# LOGGING CONFIGURATION (Lesson Learned #3)
# =====================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler() # Perfect for Render logs
    ]
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY: Read from .env, default to False in production
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-change-me-in-production')
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# =====================================================
# APPLICATION DEFINITION
# =====================================================
INSTALLED_APPS = [
    'daphne', # Must be first for Channels
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'whitenoise.runserver_nostatic',
    'cloudinary',
    'cloudinary_storage',
    'channels',

    # Local Apps
    'core',
    'tours',
    'marketplace',
    'payments',
    'blog',      
    'reports',   
    'inventory', 
]

# =====================================================
# MIDDLEWARE
# =====================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Lesson Learned: Correct placement
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'touraddis2.urls'

# =====================================================
# TEMPLATES & CONTEXT PROCESSORS
# =====================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'core.context_processors.cart', # Pre-wired for global cart access
            ],
        },
    },
]

# =====================================================
# WSGI & ASGI (WebSocket Ready)
# =====================================================
WSGI_APPLICATION = 'touraddis2.wsgi.application'
ASGI_APPLICATION = 'touraddis2.asgi.application'

# =====================================================
# DATABASE
# =====================================================
# =====================================================
# DATABASE
# =====================================================
if os.getenv('DATABASE_URL'):
    # Production: Use Render's PostgreSQL
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    # Local Development: Use PostgreSQL
   DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DATABASE_NAME', 'touraddis2_db'),
            'USER': os.getenv('DATABASE_USER', 'touraddis2_user'),
            'PASSWORD': os.getenv('DATABASE_PASSWORD', ''),
            'HOST': os.getenv('DATABASE_HOST', 'localhost'),
            'PORT': os.getenv('DATABASE_PORT', '5432'),
        }
    }

# =====================================================
# AUTH, I18N, & TIMEZONE
# =====================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en'
TIME_ZONE = 'Africa/Addis_Ababa'
USE_I18N = True
USE_TZ = True

LANGUAGES = [('en', 'English'), ('am', 'Amharic')]
LOCALE_PATHS = [BASE_DIR / 'locale']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =====================================================
# STATIC & MEDIA FILES
# =====================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Local Media Storage
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Cloudinary Configuration
#CLOUDINARY_STORAGE = {
#    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME', ''),
#    'API_KEY': os.getenv('CLOUDINARY_API_KEY', ''),
#    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET', ''),
#}

#if os.getenv('USE_CLOUDINARY', 'False') == 'True':
#    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
#    MEDIA_URL = '/media/'
#else:
#    MEDIA_URL = '/media/'
#    MEDIA_ROOT = BASE_DIR / 'media'

# =====================================================
# EMAIL CONFIGURATION
# =====================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'mail.privateemail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'TourAddis <info@touraddis.com>')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'tomibzan@gmail.com')

# =====================================================
# CART SETTINGS
# =====================================================
CART_SESSION_ID = 'cart'

# =====================================================
# SECURITY (Production Only)
# =====================================================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    
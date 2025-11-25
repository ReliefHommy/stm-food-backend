

from pathlib import Path
import os
from dotenv import load_dotenv


# -------------------------------------------------
# Base paths & env
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from project root
load_dotenv(BASE_DIR / ".env")

# Security
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'fallback-secret-for-development')



load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Use ENVIRONMENT or DEBUG flag from env
# In production, set ENVIRONMENT=production in your host.
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT != "production"


# -------------------------------------------------
# Hosts & CORS / CSRF
# -------------------------------------------------

# Backend domain + local dev


ALLOWED_HOSTS = [
    "api.somtammarket.com",
    "localhost",
    "127.0.0.1",
    ".up.railway.app",  # ← Railway auto domain
]

# Frontend origins that will call this API
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",              # local Next.js dev
    "https://somtammarket.com",           # portal / landing
    "https://www.somtammarket.com",       # www version if used
    "https://food.somtammarket.com",      # STM Food frontend
    "https://nokinhouse.tech",    # NIT studio frontend (later)
]

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True  # needed if you use cookies with JWT / sessions

CSRF_TRUSTED_ORIGINS = [
    "https://somtammarket.com",
    "https://www.somtammarket.com",
    "https://food.somtammarket.com",
    "https://nokinhouse.tech",
    "http://localhost:3000",
]



# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'thefood',
    'orders',
    'studio',
    'rest_framework',
    'corsheaders',
]

MIDDLEWARE = [
   
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
]



ROOT_URLCONF = 'stm_food_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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




WSGI_APPLICATION = "stm_food_backend.wsgi.application"

# -------------------------------------------------
# REST Framework
# -------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}




DATABASES = {
    'default': {
         "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "stm_food_dj"),
        "USER": os.getenv("POSTGRES_USER", "postgres"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}



# Custom user model
AUTH_USER_MODEL = 'thefood.User'


# -------------------------------------------------
# Password validation
# -------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# -------------------------------------------------
# i18n
# -------------------------------------------------

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True




# -------------------------------------------------
# Static & Media
# -------------------------------------------------



OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'




DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -------------------------------------------------
# Security for production
# -------------------------------------------------
if not DEBUG:
    # ✅ For now: DO NOT force HTTPS inside Django.
    # Railway already serves your app over HTTPS.
    SECURE_SSL_REDIRECT = False

    # Turn off strict cookie+HSTS for now until everything is stable
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False



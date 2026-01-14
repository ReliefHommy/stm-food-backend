

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
    "stm-food-backend-production.up.railway.app",  # ← Railway auto domain
]

# CORS (frontend -> backend API)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://somtammarket.com",
    "https://www.somtammarket.com",
    "https://food.somtammarket.com",
    "https://nokinhouse.tech",
    "https://stm-portal-frontend.vercel.app",
]




CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",
]

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True  
# CSRF trusted origins (must include scheme)
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "https://somtammarket.com",
    "https://www.somtammarket.com",
    "https://food.somtammarket.com",
    "https://nokinhouse.tech",
    "https://stm-portal-frontend.vercel.app",
]

if ENVIRONMENT == "production":
    # Ensure Railway origin is trusted for admin POST
    CSRF_TRUSTED_ORIGINS += [
        "https://stm-food-backend-production.up.railway.app",
    ] 

# -------------------------------------------------
# Proxy / HTTPS awareness (Railway)
# -------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# -------------------------------------------------
# Cookie domain (IMPORTANT)
# -------------------------------------------------
# Only set COOKIE_DOMAIN when you're serving the backend on your own domain.
# DO NOT set it when accessing admin via *.up.railway.app.
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN", "").strip() or None
CSRF_COOKIE_DOMAIN = COOKIE_DOMAIN
SESSION_COOKIE_DOMAIN = COOKIE_DOMAIN

# -------------------------------------------------
# Cookies for admin + session
# -------------------------------------------------
# Admin login uses CSRF + session cookies. Keep them consistent.
# If SameSite=None, cookies MUST be Secure=True in modern browsers.
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SECURE = (ENVIRONMENT == "production")
SESSION_COOKIE_SECURE = (ENVIRONMENT == "production")



CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SAMESITE = "None"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Ensure the production backend domain is trusted (useful when running on Railway)
if ENVIRONMENT == "production":
    # Railway terminates HTTPS at the proxy, so don't force redirect here.
    SECURE_SSL_REDIRECT = False





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
        "NAME": os.getenv("POSTGRES_DB", "railway"),
        "USER": os.getenv("POSTGRES_USER", "postgres"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
        "HOST": os.getenv("POSTGRES_HOST", "caboose.proxy.rlwy.net"),
        "PORT": os.getenv("POSTGRES_PORT", "24124"),
    }
}



# Custom user model
AUTH_USER_MODEL = 'thefood.User'

# Ensure Django admin and session-based auth continue to work alongside any API/backends.
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    # Add any custom backends for API auth below (keep them after ModelBackend)
]

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



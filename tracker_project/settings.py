from pathlib import Path
import dj_database_url
import os
from dotenv import load_dotenv

load_dotenv(override=True)
print("DEBUG settings.py: .env loaded with override=True")

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'fallback_secret_key_insecure_dev_only')
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

print(f"DEBUG settings.py: SECRET_KEY loaded: {'******' if SECRET_KEY != 'fallback_secret_key_insecure_dev_only' else 'FALLBACK'}")
print(f"DEBUG settings.py: DEBUG mode: {DEBUG}")

ALLOWED_HOSTS = []
railway_app_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN') or os.environ.get('ALLOWED_HOST_FQDN')

if railway_app_domain:
    ALLOWED_HOSTS.append(railway_app_domain)
    print(f"DEBUG settings.py: Added Railway domain to ALLOWED_HOSTS: {railway_app_domain}")

if DEBUG:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])
    print(f"DEBUG settings.py: Added localhost/127.0.0.1 to ALLOWED_HOSTS for DEBUG.")
elif not ALLOWED_HOSTS:
    print("WARNING settings.py: No production host in env (RAILWAY_PUBLIC_DOMAIN/ALLOWED_HOST_FQDN). ALLOWED_HOSTS might be empty.")
    # ALLOWED_HOSTS.append('*') # Consider for initial deployment only if necessary

ALLOWED_HOSTS = list(set(filter(None, ALLOWED_HOSTS)))
print(f"DEBUG settings.py: Final ALLOWED_HOSTS: {ALLOWED_HOSTS}")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'rest_framework',
    'flights',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tracker_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'tracker_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DATABASE_URL_FROM_ENV = os.environ.get('DATABASE_URL')
print(f"DEBUG settings.py: DATABASE_URL from os.environ: {DATABASE_URL_FROM_ENV}")

if DATABASE_URL_FROM_ENV:
    try:
        DATABASES['default'] = dj_database_url.config(
            default=DATABASE_URL_FROM_ENV,
            conn_max_age=600,
            ssl_require=True
        )
        print(f"DEBUG settings.py: DATABASES['default'] configured from DATABASE_URL.")
        print(f"DEBUG settings.py:   HOST: {DATABASES['default'].get('HOST')}")
        print(f"DEBUG settings.py:   PORT: {DATABASES['default'].get('PORT')}")
        print(f"DEBUG settings.py:   NAME: {DATABASES['default'].get('NAME')}")
        print(f"DEBUG settings.py:   USER: {DATABASES['default'].get('USER')}")
    except Exception as e:
        print(f"ERROR settings.py: Failed to configure database from DATABASE_URL: {e}. Falling back to SQLite.")
else:
    print("DEBUG settings.py: DATABASE_URL not found in environment. Using SQLite as fallback.")

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'api_cache_table',
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '{levelname} {asctime} {module}: {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'flights.services': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'flights.management.commands': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}
print("DEBUG settings.py: Settings file loaded completely.")
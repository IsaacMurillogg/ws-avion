# tracker_project/settings.py

from pathlib import Path
import dj_database_url
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env (¡IMPORTANTE que esté al principio!)
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Claves y Debug ---
# Obtener la clave secreta de las variables de entorno
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'una-clave-secreta-de-fallback-solo-para-emergencias')
# Obtener el estado de DEBUG de las variables de entorno
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True' # 'False' como default más seguro

# --- Allowed Hosts ---
ALLOWED_HOSTS = []
RAILWAY_STATIC_URL = os.environ.get('RAILWAY_STATIC_URL') # Usado para el host de Railway
APP_HOSTNAME = os.environ.get('RAILWAY_PUBLIC_DOMAIN') # Variable que Railway puede proveer para el dominio público de la app
# O puedes usar ALLOWED_HOST_FQDN como lo tenías, si la defines en Railway

if APP_HOSTNAME:
    ALLOWED_HOSTS.append(APP_HOSTNAME)
elif RAILWAY_STATIC_URL: # Fallback si RAILWAY_PUBLIC_DOMAIN no está
    # RAILWAY_STATIC_URL suele ser para estáticos, no el host principal de la app,
    # pero si es lo que tienes configurado para el dominio de la app, úsalo.
    # Un nombre de host típico de Railway sería algo como: mi-app.up.railway.app
    try:
        ALLOWED_HOSTS.append(RAILWAY_STATIC_URL.split('//')[1].split(':')[0]) # Quita http y puerto
    except IndexError:
        pass # Manejar si el formato no es el esperado

if DEBUG:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])
else:
    # Para producción, asegúrate de que tu dominio de Railway o personalizado esté aquí.
    # Si usas una variable específica para el FQDN en Railway (ej. ALLOWED_HOST_FQDN), úsala:
    production_host = os.environ.get('ALLOWED_HOST_FQDN')
    if production_host:
        ALLOWED_HOSTS.append(production_host)
    # Es buena práctica no usar '*' en producción si puedes evitarlo.
    if not ALLOWED_HOSTS and not DEBUG: # Si no hay hosts y no estamos en DEBUG
        ALLOWED_HOSTS.append('*') # Como último recurso, pero intenta ser específico

# Asegúrate de que no haya duplicados y limpia la lista (por si acaso)
ALLOWED_HOSTS = list(set(host for host in ALLOWED_HOSTS if host))


# --- Aplicaciones Instaladas ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'flights',
    # 'whitenoise.runserver_nostatic', # Solo para desarrollo si usas `python manage.py runserver` con WhiteNoise
]

# --- Middleware ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Asegúrate de tener 'whitenoise' en requirements.txt
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

# --- Base de Datos ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Fallback si no hay DATABASE_URL
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DATABASE_URL_ENV = os.environ.get('DATABASE_URL')
if DATABASE_URL_ENV:
    DATABASES['default'] = dj_database_url.config(
        default=DATABASE_URL_ENV, # Usa la variable directamente
        conn_max_age=600,
        ssl_require=True # Para Railway, SSL suele ser requerido/recomendado para conexiones públicas. Prueba con True. Si falla, prueba False.
    )

# --- Validación de Contraseñas ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internacionalización ---
LANGUAGE_CODE = 'es-mx' # Cambiado a español de México como ejemplo
TIME_ZONE = 'America/Mexico_City' # Ejemplo
USE_I18N = True
USE_TZ = True # Importante para manejar correctamente las zonas horarias

# --- Archivos Estáticos ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # Directorio para collectstatic
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage' # Para WhiteNoise

# --- Tipo de Clave Primaria por Defecto ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Django REST Framework ---
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}

# --- Caché ---
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'api_cache_table',
    }
}

# --- Logging ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {asctime} {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'flights.services': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'flights.management.commands': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        }
    },
}
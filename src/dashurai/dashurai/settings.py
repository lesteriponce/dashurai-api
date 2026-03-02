import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    'django_ratelimit',
    'wagtail',
    'wagtail.admin',
    'wagtail.documents',
    'wagtail.users',
    'wagtail.images',
    'wagtail.search',
    'wagtail.sites',
    'wagtail.contrib.forms',
    'wagtail.contrib.redirects',
    'modelcluster',
    'taggit',
    'users',
    'careers',
    'contact',
    'cms',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'utils.middleware.RequestLoggingMiddleware',
    'utils.middleware.SecurityLoggingMiddleware',
]

ROOT_URLCONF = 'dashurai.urls'

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

WSGI_APPLICATION = 'dashurai.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
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


# Internationalization
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# drf-spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'DashurAI API',
    'DESCRIPTION': 'Django REST API with Wagtail CMS integration',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_TOKEN_LIFETIME', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=config('JWT_REFRESH_TOKEN_LIFETIME', default=1440, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}

# CORS Settings
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS', 
    default='http://localhost:5173,http://127.0.0.1:5173',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

CORS_ALLOW_CREDENTIALS = True

# Wagtail Settings
WAGTAIL_SITE_NAME = 'Dashurai AI'
WAGTAILADMIN_BASE_URL = 'http://localhost:8000'

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Rate Limiting Settings
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Fallback to file cache if Redis is not available
try:
    import redis
except ImportError:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': '/tmp/django_cache',
        }
    }

# Rate limiting configurations (requests per time period)
RATELIMIT_VIEW_CONFIG = {
    'auth': {
        'login': '5/m',  # 5 login attempts per minute
        'register': '3/m',  # 3 registration attempts per minute
        'refresh': '10/m',  # 10 token refresh attempts per minute
    },
    'public': {
        'contact': '2/m',  # 2 contact submissions per minute
        'job_application': '3/h',  # 3 job applications per hour
        'careers_list': '30/m',  # 30 career list requests per minute
    },
    'cms': {
        'public_pages': '60/m',  # 60 public page requests per minute
        'documents': '30/m',  # 30 document requests per minute
        'images': '60/m',  # 60 image requests per minute
    }
}

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'detailed': {
            'format': '[{asctime}] {levelname} [{name}:{lineno}] {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'console_production': {
            'level': 'WARNING',
            'filters': ['require_debug_false'],
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'detailed',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django_error.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 1024*1024*5,  # 5MB
            'backupCount': 5,
            'formatter': 'detailed',
        },
        'api_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'api.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'console_production', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'wagtail': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'rest_framework': {
            'handlers': ['api_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'api': {
            'handlers': ['api_file', 'console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'users': {
            'handlers': ['security_file', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'careers': {
            'handlers': ['api_file', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'contact': {
            'handlers': ['api_file', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'cms': {
            'handlers': ['api_file', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'console_production', 'file'],
        'level': 'INFO',
    },
}

# Create logs directory if it doesn't exist
import os
LOGS_DIR = BASE_DIR / 'logs'
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR, exist_ok=True)

"""
Development settings
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Development-specific apps
INSTALLED_APPS += [
    'django_extensions',
    'debug_toolbar',
    'silk',
]

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'silk.middleware.SilkyMiddleware',
]

# Internal IPs for Debug Toolbar
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Email Backend (Console for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Disable template caching
TEMPLATES[0]['OPTIONS']['debug'] = True

# SQL Query Logging
LOGGING['loggers']['django.db.backends'] = {
    'level': 'DEBUG',
    'handlers': ['console'],
}

# Celery - Eager execution in development (synchronous)
CELERY_TASK_ALWAYS_EAGER = config('CELERY_ALWAYS_EAGER', default=True, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = True

print(f"🚀 Running in DEVELOPMENT mode")
print(f"📊 Debug Toolbar: http://localhost:8000/__debug__/")
print(f"🎯 Silk Profiler: http://localhost:8000/silk/")

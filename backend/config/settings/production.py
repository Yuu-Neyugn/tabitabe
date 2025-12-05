"""
Production settings
"""
from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

DEBUG = False

# Security Settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Force HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://maps.googleapis.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "data:")

# Logging to file
LOGGING['handlers']['file']['filename'] = '/var/log/tabitabe/django.log'

# Sentry for error tracking
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        environment=config('SENTRY_ENVIRONMENT', default='production'),
        traces_sample_rate=0.1,
        send_default_pii=False,
    )

# Email Backend (Production)
EMAIL_BACKEND = 'anymail.backends.mailgun.EmailBackend'

# Force MinIO/S3 storage
USE_S3 = True

# Celery - Production configuration
CELERY_TASK_ALWAYS_EAGER = False

print("🚀 Running in PRODUCTION mode")

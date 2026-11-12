from .base import *  # noqa: F403

DEBUG = True

# In development, accept localhost testing
ALLOWED_HOSTS = ['*']

# Simple static files in dev
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'


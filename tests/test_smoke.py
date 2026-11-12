import pytest
from django.conf import settings


@pytest.mark.django_db
def test_environment_and_settings_loaded():
    """Verify that Django settings are properly loaded from the modular configuration."""
    assert settings.TIME_ZONE == 'Asia/Kathmandu'
    assert 'rest_framework' in settings.INSTALLED_APPS
    assert 'django_htmx' in settings.INSTALLED_APPS


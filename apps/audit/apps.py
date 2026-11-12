from django.apps import AppConfig


class AuditConfig(AppConfig):
    """Configuration for the audit logging and traceability application."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.audit'
    verbose_name = 'Audit & Security Logs'


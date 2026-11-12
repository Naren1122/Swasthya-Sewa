from django.contrib import admin
from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    """
    Read-only Django Admin interface for forensic audit logs.
    Enforces US-11: Audit records cannot be created, modified, or deleted via the UI.
    """
    list_display = (
        'timestamp',
        'action',
        'actor_display',
        'target_type',
        'target_id',
        'ip_address',
    )
    list_filter = (
        'action',
        'target_type',
        'timestamp',
    )
    search_fields = (
        'actor_email',
        'actor__email',
        'actor__first_name',
        'actor__last_name',
        'target_id',
        'ip_address',
        'description',
    )
    ordering = ('-timestamp',)
    list_select_related = ('actor',)
    readonly_fields = [field.name for field in AuditEvent._meta.fields]

    @admin.display(description='Actor')
    def actor_display(self, obj):
        if obj.actor:
            return f"{obj.actor.full_name} ({obj.actor.email})"
        return obj.actor_email or 'Anonymous / System'

    def has_add_permission(self, request):
        """Audit logs can only be created programmatically, never manually via admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Audit logs are immutable; cannot be edited."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Audit logs cannot be deleted."""
        return False


import uuid
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import models
from django.utils import timezone


class AuditAction(models.TextChoices):
    # Authentication & Session Events
    LOGIN_SUCCESS = 'LOGIN_SUCCESS', 'Login Successful'
    LOGIN_FAILED = 'LOGIN_FAILED', 'Login Failed'
    LOGOUT = 'LOGOUT', 'Logout'
    PASSWORD_CHANGE = 'PASSWORD_CHANGE', 'Password Changed'
    ACCESS_DENIED = 'ACCESS_DENIED', 'Access Denied / 403 Forbidden'

    # Account & RBAC Changes
    USER_REGISTERED = 'USER_REGISTERED', 'User Registered'
    ROLE_CHANGED = 'ROLE_CHANGED', 'User Role Modified'
    ACCOUNT_DEACTIVATED = 'ACCOUNT_DEACTIVATED', 'Account Deactivated'
    ACCOUNT_ACTIVATED = 'ACCOUNT_ACTIVATED', 'Account Activated'

    # Domain Record Modifications
    RECORD_CREATED = 'RECORD_CREATED', 'Record Created'
    RECORD_UPDATED = 'RECORD_UPDATED', 'Record Updated'
    RECORD_DELETED = 'RECORD_DELETED', 'Record Deleted'


class AuditEvent(models.Model):
    """
    Immutable audit log entry recording security and operational events.
    Adheres strictly to PRD FR-20 and US-11 (Auditable state changes).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_events',
        help_text='User who initiated the action (null if anonymous or unauthenticated)',
    )
    actor_email = models.CharField(
        max_length=255,
        blank=True,
        help_text='Preserved email snapshot in case the actor account is deleted',
    )
    action = models.CharField(
        max_length=50,
        choices=AuditAction.choices,
        db_index=True,
    )
    target_type = models.CharField(
        max_length=100,
        blank=True,
        help_text='Domain model affected (e.g. User, PatientProfile, Appointment)',
    )
    target_id = models.CharField(
        max_length=64,
        blank=True,
        help_text='Primary key or identifier of the affected target record',
    )
    description = models.TextField(
        blank=True,
        help_text='Human-readable summary of the action taken',
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the client request',
    )
    user_agent = models.TextField(
        blank=True,
        help_text='Client browser / device information',
    )
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='Structured contextual metadata (never store sensitive passwords or tokens)',
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        editable=False,
    )

    class Meta:
        verbose_name = 'Audit Event'
        verbose_name_plural = 'Audit Events'
        ordering = ['-timestamp']

    def __str__(self):
        actor_str = self.actor_email or (str(self.actor) if self.actor else 'Anonymous')
        return f"[{self.timestamp:%Y-%m-%d %H:%M:%S}] {actor_str} -> {self.get_action_display()}"

    def save(self, *args, **kwargs):
        # Auto-snapshot actor's email if not already specified
        if self.actor and not self.actor_email:
            self.actor_email = getattr(self.actor, 'email', '')

        # Enforce immutability: once written, audit logs cannot be altered (US-11)
        if self._state.adding is False and AuditEvent.objects.filter(pk=self.pk).exists():
            raise PermissionDenied('Audit records are immutable and cannot be updated.')

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Enforce immutability: audit logs cannot be deleted
        raise PermissionDenied('Audit records are permanent and cannot be deleted.')


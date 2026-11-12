import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

from apps.audit.models import AuditAction, AuditEvent
from apps.audit.services import get_client_ip, get_user_agent, log_audit_event

User = get_user_model()


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
class TestAuditLogging:
    """Unit tests for the audit logging system (PRD FR-20, US-11)."""

    def test_log_audit_event_creates_record(self):
        user = User.objects.create_user(
            email='audit.actor@hospital.org',
            password='SecurePass123!',
        )
        event = log_audit_event(
            action=AuditAction.LOGIN_SUCCESS,
            actor=user,
            description='Successful login from staff terminal.',
            extra_data={'department': 'Cardiology'},
        )

        assert event.id is not None
        assert event.actor == user
        assert event.actor_email == 'audit.actor@hospital.org'
        assert event.action == AuditAction.LOGIN_SUCCESS
        assert event.description == 'Successful login from staff terminal.'
        assert event.extra_data == {'department': 'Cardiology'}
        assert event.timestamp is not None
        assert 'audit.actor@hospital.org' in str(event)

    def test_log_audit_event_with_request_metadata(self, rf):
        request = rf.get(
            '/',
            REMOTE_ADDR='192.168.10.55',
            HTTP_USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        )
        user = User.objects.create_user(email='clinician@hosp.org', password='p')
        request.user = user

        event = log_audit_event(
            action=AuditAction.RECORD_CREATED,
            request=request,
            target_type='PatientProfile',
            target_id='PAT-2026-001',
        )

        assert event.actor == user
        assert event.ip_address == '192.168.10.55'
        assert 'Windows NT 10.0' in event.user_agent
        assert event.target_type == 'PatientProfile'
        assert event.target_id == 'PAT-2026-001'

    def test_client_ip_reverse_proxy_extraction(self, rf):
        request = rf.get(
            '/',
            HTTP_X_FORWARDED_FOR='203.0.113.195, 10.0.0.1',
            REMOTE_ADDR='10.0.0.1',
        )
        assert get_client_ip(request) == '203.0.113.195'

    def test_audit_event_immutability_update_prevented(self):
        event = log_audit_event(
            action=AuditAction.ROLE_CHANGED,
            description='Original audit log.',
        )
        # Attempting to modify existing audit record must raise PermissionDenied
        event.description = 'Tampered log attempt!'
        with pytest.raises(PermissionDenied, match='immutable'):
            event.save()

    def test_audit_event_immutability_delete_prevented(self):
        event = log_audit_event(
            action=AuditAction.ACCOUNT_DEACTIVATED,
            description='Deactivated staff member.',
        )
        # Attempting to delete audit record must raise PermissionDenied
        with pytest.raises(PermissionDenied, match='permanent and cannot be deleted'):
            event.delete()

    def test_anonymous_failed_login_event(self, rf):
        request = rf.post('/login/', REMOTE_ADDR='45.33.32.156')
        event = log_audit_event(
            action=AuditAction.LOGIN_FAILED,
            request=request,
            description='Failed login attempt for unknown@hosp.org.',
            extra_data={'attempted_email': 'unknown@hosp.org'},
        )

        assert event.actor is None
        assert event.ip_address == '45.33.32.156'
        assert 'Anonymous' in str(event)


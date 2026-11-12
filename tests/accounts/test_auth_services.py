from unittest.mock import MagicMock
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import RequestFactory
from django.urls import reverse

from apps.accounts.models import Gender, PatientProfile, Role
from apps.accounts.permissions import (
    IsAdmin,
    IsDoctor,
    IsPatient,
    IsReceptionist,
    IsSelfOrAdmin,
    role_required,
)
from apps.accounts.services import (
    authenticate_and_login_user,
    get_redirect_url_for_user,
    logout_user,
    register_patient,
)

User = get_user_model()


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
class TestAuthServices:
    """Tests for authentication and login service layer."""

    def test_authenticate_and_login_successful(self, rf):
        user = User.objects.create_user(
            email='testuser@hospital.org',
            password='SecretPassword123!',
        )
        request = rf.post('/login/')
        session = SessionStore()
        session.create()
        request.session = session
        request._messages = MagicMock()

        logged_user = authenticate_and_login_user(request, 'testuser@hospital.org', 'SecretPassword123!')
        assert logged_user == user
        assert '_auth_user_id' in request.session

    def test_authenticate_invalid_password_fails(self, rf):
        User.objects.create_user(
            email='active@hospital.org',
            password='CorrectPassword!',
        )
        request = rf.post('/login/')
        session = SessionStore()
        session.create()
        request.session = session

        with pytest.raises(ValidationError, match='Invalid email or password.'):
            authenticate_and_login_user(request, 'active@hospital.org', 'WrongPassword!')

    def test_authenticate_deactivated_user_fails(self, rf):
        user = User.objects.create_user(
            email='inactive@hospital.org',
            password='ValidPassword123!',
        )
        user.is_active = False
        user.save()

        request = rf.post('/login/')
        session = SessionStore()
        session.create()
        request.session = session

        with pytest.raises(ValidationError, match='This account has been deactivated.'):
            authenticate_and_login_user(request, 'inactive@hospital.org', 'ValidPassword123!')

    def test_role_based_redirect_urls(self):
        anon = AnonymousUser()
        assert get_redirect_url_for_user(anon) == reverse('accounts:login')

        admin_user = User.objects.create_superuser(email='adm@medicore.org', password='p')
        assert get_redirect_url_for_user(admin_user) == '/admin/'

        doctor = User.objects.create_user(email='doc@medicore.org', password='p', role=Role.DOCTOR)
        assert get_redirect_url_for_user(doctor) == '/doctor/dashboard/'

        receptionist = User.objects.create_user(email='rec@medicore.org', password='p', role=Role.RECEPTIONIST)
        assert get_redirect_url_for_user(receptionist) == '/reception/dashboard/'

        patient = User.objects.create_user(email='pat@medicore.org', password='p', role=Role.PATIENT)
        assert get_redirect_url_for_user(patient) == '/portal/dashboard/'

    def test_register_patient_service_atomic_success(self):
        user, profile = register_patient(
            email='newpatient@nepal.org',
            password='PatientSecret123!',
            first_name='Anil',
            last_name='Gurung',
            phone_number='9801234567',
            gender=Gender.MALE,
            address='Pokhara Ward 8',
            emergency_contact_name='Sunita Gurung',
            emergency_contact_phone='9807654321',
            emergency_contact_relation='Sister',
        )

        assert user.email == 'newpatient@nepal.org'
        assert user.role == Role.PATIENT
        assert profile.user == user
        assert profile.patient_number.startswith('PAT-')
        assert profile.gender == Gender.MALE
        assert profile.emergency_contact_name == 'Sunita Gurung'

    def test_register_patient_duplicate_email_rejected(self):
        register_patient(
            email='alreadyexists@nepal.org',
            password='Pass1!',
            first_name='A',
            last_name='B',
        )
        with pytest.raises(ValidationError, match='already exists'):
            register_patient(
                email='alreadyexists@nepal.org',
                password='Pass2!',
                first_name='C',
                last_name='D',
            )


@pytest.mark.django_db
class TestPermissionsAndDecorators:
    """Tests for DRF permission classes and @role_required decorator."""

    def test_drf_role_permissions(self, rf):
        doctor = User.objects.create_user(email='doc2@med.org', password='p', role=Role.DOCTOR)
        patient = User.objects.create_user(email='pat2@med.org', password='p', role=Role.PATIENT)

        req_doc = rf.get('/')
        req_doc.user = doctor

        req_pat = rf.get('/')
        req_pat.user = patient

        # IsDoctor check
        assert IsDoctor().has_permission(req_doc, None) is True
        assert IsDoctor().has_permission(req_pat, None) is False

        # IsPatient check
        assert IsPatient().has_permission(req_pat, None) is True
        assert IsPatient().has_permission(req_doc, None) is False

    def test_idor_protection_is_self_or_admin(self, rf):
        user1 = User.objects.create_user(email='user1@med.org', password='p', role=Role.PATIENT)
        user2 = User.objects.create_user(email='user2@med.org', password='p', role=Role.PATIENT)
        admin = User.objects.create_superuser(email='boss@med.org', password='p')

        profile1 = PatientProfile.objects.create(user=user1, patient_number='PAT-1')
        profile2 = PatientProfile.objects.create(user=user2, patient_number='PAT-2')

        perm = IsSelfOrAdmin()

        # User 1 accessing own profile -> Allowed
        req1 = rf.get('/')
        req1.user = user1
        assert perm.has_object_permission(req1, None, profile1) is True

        # User 1 attempting to access User 2's profile -> FORBIDDEN (IDOR prevented)
        assert perm.has_object_permission(req1, None, profile2) is False

        # Admin accessing User 2's profile -> Allowed
        req_admin = rf.get('/')
        req_admin.user = admin
        assert perm.has_object_permission(req_admin, None, profile2) is True

    def test_role_required_decorator(self, rf):
        @role_required(Role.DOCTOR)
        def doctor_endpoint(request):
            return 'doctor_access_granted'

        doctor = User.objects.create_user(email='doc3@med.org', password='p', role=Role.DOCTOR)
        patient = User.objects.create_user(email='pat3@med.org', password='p', role=Role.PATIENT)

        # 1. Doctor access -> OK
        req_doc = rf.get('/')
        req_doc.user = doctor
        assert doctor_endpoint(req_doc) == 'doctor_access_granted'

        # 2. Patient access -> PermissionDenied (403)
        req_pat = rf.get('/')
        req_pat.user = patient
        with pytest.raises(PermissionDenied):
            doctor_endpoint(req_pat)

        # 3. Unauthenticated access -> Redirect to login
        req_anon = rf.get('/')
        req_anon.user = AnonymousUser()
        response = doctor_endpoint(req_anon)
        assert response.status_code == 302
        assert response.url == reverse('accounts:login')


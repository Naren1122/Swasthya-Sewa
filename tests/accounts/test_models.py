from datetime import date
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from apps.accounts.models import BloodGroup, Gender, PatientProfile, Role, StaffProfile

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Unit tests for the custom User model and UserManager."""

    def test_create_user_successful(self):
        user = User.objects.create_user(
            email='patient@example.com',
            password='Password123!',
            first_name='Aayush',
            last_name='Shrestha',
        )
        assert user.email == 'patient@example.com'
        assert user.first_name == 'Aayush'
        assert user.last_name == 'Shrestha'
        assert user.full_name == 'Aayush Shrestha'
        assert user.role == Role.PATIENT
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        # Password must be securely hashed
        assert user.password != 'Password123!'
        assert user.check_password('Password123!') is True

    def test_create_user_email_lowercased_and_normalized(self):
        user = User.objects.create_user(
            email='Dr.Ramesh@Hospital.NP',
            password='SecurePass456!',
            role=Role.DOCTOR,
        )
        assert user.email == 'dr.ramesh@hospital.np'

    def test_create_user_without_email_raises_error(self):
        with pytest.raises(ValueError, match='An email address is required.'):
            User.objects.create_user(email='', password='password123')

    def test_create_superuser_successful(self):
        admin_user = User.objects.create_superuser(
            email='admin@hospital.org',
            password='AdminPassword123!',
            first_name='Hospital',
            last_name='Admin',
        )
        assert admin_user.email == 'admin@hospital.org'
        assert admin_user.is_staff is True
        assert admin_user.is_superuser is True
        assert admin_user.role == Role.ADMIN
        assert admin_user.is_admin is True

    def test_create_superuser_invalid_flags(self):
        with pytest.raises(ValueError, match='Superuser must have is_staff=True.'):
            User.objects.create_superuser(
                email='fakeadmin@test.com',
                password='pass',
                is_staff=False,
            )

        with pytest.raises(ValueError, match='Superuser must have is_superuser=True.'):
            User.objects.create_superuser(
                email='fakeadmin2@test.com',
                password='pass',
                is_superuser=False,
            )

    def test_case_insensitive_duplicate_email_rejected(self):
        User.objects.create_user(
            email='unique@medicore.org',
            password='Password123!',
        )
        # Attempting to create duplicate with different casing must fail
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email='UNIQUE@medicore.org',
                password='Password456!',
            )

    def test_role_properties(self):
        doctor = User.objects.create_user(
            email='doc@medicore.org',
            password='pass',
            role=Role.DOCTOR,
        )
        receptionist = User.objects.create_user(
            email='rec@medicore.org',
            password='pass',
            role=Role.RECEPTIONIST,
        )

        assert doctor.is_doctor is True
        assert doctor.is_patient is False
        assert receptionist.is_receptionist is True
        assert receptionist.is_doctor is False


@pytest.mark.django_db
class TestPatientProfileModel:
    """Unit tests for the PatientProfile model."""

    def test_patient_profile_creation_and_age_computation(self):
        user = User.objects.create_user(
            email='sita.sharma@example.com',
            password='Pass!',
            first_name='Sita',
            last_name='Sharma',
            role=Role.PATIENT,
        )
        profile = PatientProfile.objects.create(
            user=user,
            patient_number='PAT-2026-00001',
            date_of_birth=date(1995, 5, 10),
            gender=Gender.FEMALE,
            blood_group=BloodGroup.O_POSITIVE,
            address='Kathmandu Ward 4',
            emergency_contact_name='Hari Sharma',
            emergency_contact_phone='9841234567',
            emergency_contact_relation='Spouse',
        )

        assert profile.patient_number == 'PAT-2026-00001'
        assert profile.gender == Gender.FEMALE
        assert profile.blood_group == BloodGroup.O_POSITIVE
        assert profile.age is not None
        assert profile.age >= 30  # 1995 to 2026
        assert str(profile) == 'PAT-2026-00001 — Sita Sharma'


@pytest.mark.django_db
class TestStaffProfileModel:
    """Unit tests for the StaffProfile model."""

    def test_staff_profile_creation(self):
        user = User.objects.create_user(
            email='dr.karki@medicore.org',
            password='DocPass123!',
            first_name='Bibek',
            last_name='Karki',
            role=Role.DOCTOR,
        )
        staff = StaffProfile.objects.create(
            user=user,
            employee_id='EMP-2026-101',
            department_name='Cardiology',
            designation='Consultant Cardiologist',
            license_number='NMC-98765',
            qualification='MBBS, MD Cardiology',
        )

        assert staff.employee_id == 'EMP-2026-101'
        assert staff.license_number == 'NMC-98765'
        assert staff.user.is_active is True
        assert 'Bibek Karki' in str(staff)


import uuid
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone
from .models import PatientProfile, Role, User

ROLE_REDIRECT_URLS = {
    Role.DOCTOR: '/doctor/dashboard/',
    Role.RECEPTIONIST: '/reception/dashboard/',
    Role.NURSE: '/nurse/dashboard/',
    Role.LAB_TECHNICIAN: '/lab/dashboard/',
    Role.PHARMACIST: '/pharmacy/dashboard/',
    Role.BILLING: '/billing/dashboard/',
    Role.PATIENT: '/portal/dashboard/',
}

DUPLICATE_EMAIL_MESSAGE = 'An account with this email address already exists.'
PATIENT_NUMBER_MAX_ATTEMPTS = 5


def get_redirect_url_for_user(user: User) -> str:
    """
    Determines the landing dashboard URL based on the user's role.
    Complies with PRD §3 role-based workspace segregation.
    """
    if not user.is_authenticated:
        return reverse('accounts:login')

    if user.is_admin:
        return reverse('admin:index')

    return ROLE_REDIRECT_URLS.get(user.role, '/portal/dashboard/')


def authenticate_and_login_user(request, email: str, password: str) -> User:
    """
    Authenticates a user by email and password and creates an active session.
    Raises ValidationError if authentication fails or account is deactivated.
    """
    if not email or not password:
        raise ValidationError('Both email and password are required.')

    clean_email = email.strip().lower()
    user = authenticate(request, email=clean_email, password=password)

    if user is None:
        # Check if credentials are valid but the account was deactivated
        existing_user = User.objects.filter(email=clean_email).first()
        if existing_user and existing_user.check_password(password) and not existing_user.is_active:
            raise ValidationError('This account has been deactivated. Please contact hospital administration.')
        raise ValidationError('Invalid email or password.')

    login(request, user)
    return user


def logout_user(request) -> None:
    """Logs out the user and flushes session data."""
    logout(request)


def generate_unique_patient_number() -> str:
    """
    Generates a unique hospital patient number (MRN).
    Format: PAT-{YEAR}-{6_HEX_CHARS} (e.g., PAT-2026-A1B2C3)
    """
    year = timezone.localdate().year
    unique_suffix = uuid.uuid4().hex[:6].upper()
    return f"PAT-{year}-{unique_suffix}"


@transaction.atomic
def register_patient(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    phone_number: str = '',
    date_of_birth=None,
    gender: str = '',
    address: str = '',
    emergency_contact_name: str = '',
    emergency_contact_phone: str = '',
    emergency_contact_relation: str = '',
) -> tuple[User, PatientProfile]:
    """
    Atomic service to register a patient and generate their demographic profile.
    Safely retries MRN generation under concurrent collisions.
    """
    clean_email = email.strip().lower()
    if User.objects.filter(email=clean_email).exists():
        raise ValidationError(DUPLICATE_EMAIL_MESSAGE)

    user = User.objects.create_user(
        email=clean_email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        role=Role.PATIENT,
    )

    profile = None
    for _ in range(PATIENT_NUMBER_MAX_ATTEMPTS):
        patient_number = generate_unique_patient_number()
        try:
            with transaction.atomic():
                profile = PatientProfile.objects.create(
                    user=user,
                    patient_number=patient_number,
                    date_of_birth=date_of_birth,
                    gender=gender,
                    address=address,
                    emergency_contact_name=emergency_contact_name,
                    emergency_contact_phone=emergency_contact_phone,
                    emergency_contact_relation=emergency_contact_relation,
                )
            break
        except IntegrityError:
            continue

    if profile is None:
        raise ValidationError('Unable to generate a unique patient number. Please try again.')

    return user, profile

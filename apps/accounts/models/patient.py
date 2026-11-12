import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .user import Role


class Gender(models.TextChoices):
    MALE = 'MALE', 'Male'
    FEMALE = 'FEMALE', 'Female'
    OTHER = 'OTHER', 'Other'


class BloodGroup(models.TextChoices):
    A_POSITIVE = 'A+', 'A+'
    A_NEGATIVE = 'A-', 'A-'
    B_POSITIVE = 'B+', 'B+'
    B_NEGATIVE = 'B-', 'B-'
    AB_POSITIVE = 'AB+', 'AB+'
    AB_NEGATIVE = 'AB-', 'AB-'
    O_POSITIVE = 'O+', 'O+'
    O_NEGATIVE = 'O-', 'O-'
    UNKNOWN = 'UNKNOWN', 'Unknown'


def validate_date_not_in_future(value):
    if value and value > timezone.localdate():
        raise ValidationError('Date cannot be in the future.')


class PatientProfile(models.Model):
    """
    Patient demographics and emergency contact (FR-03, US-01).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_profile',
    )
    patient_number = models.CharField(
        max_length=32,
        unique=True,
        help_text='Unique hospital patient record number / MRN (e.g., PAT-2026-A1B2C3)',
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        validators=[validate_date_not_in_future],
    )
    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        blank=True,
    )
    blood_group = models.CharField(
        max_length=10,
        choices=BloodGroup.choices,
        default=BloodGroup.UNKNOWN,
    )
    address = models.TextField(
        blank=True,
        help_text='Residential address (Municipality, Ward, District)',
    )

    # Emergency contact (FR-03, US-01)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relation = models.CharField(
        max_length=50,
        blank=True,
        help_text='Relationship (e.g., Parent, Spouse, Sibling, Guardian)',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Patient Profile'
        verbose_name_plural = 'Patient Profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient_number} — {self.user.full_name}"

    def clean(self):
        super().clean()
        if self.user_id and self.user.role != Role.PATIENT:
            raise ValidationError(
                {'user': 'A patient profile can only belong to a user with the Patient role.'}
            )

    @property
    def age(self):
        """Current age in years, or None if the date of birth is unknown."""
        if not self.date_of_birth:
            return None
        today = timezone.localdate()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .user import STAFF_ROLES


class StaffProfile(models.Model):
    """
    Professional details for hospital staff: doctors, receptionists, nurses,
    laboratory technicians, pharmacists and billing staff.

    Whether a person can log in is controlled by User.is_active.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_profile',
    )
    employee_id = models.CharField(
        max_length=32,
        unique=True,
        help_text='Unique hospital staff/employee identifier (e.g., EMP-2026-001)',
    )
    department_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='Assigned department (e.g. Cardiology, OPD Reception, Central Laboratory)',
    )
    designation = models.CharField(
        max_length=100,
        blank=True,
        help_text='Job title or clinical rank (e.g. Consultant Physician, Senior Pharmacist)',
    )
    license_number = models.CharField(
        max_length=50,
        blank=True,
        help_text='Professional council registration (e.g., NMC number for doctors, NPC for pharmacists)',
    )
    qualification = models.CharField(
        max_length=200,
        blank=True,
        help_text='Academic and professional credentials (e.g., MBBS, MD, B.Pharm)',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Staff Profile'
        verbose_name_plural = 'Staff Profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee_id} — {self.user.full_name} ({self.designation or self.user.get_role_display()})"

    def clean(self):
        super().clean()
        if self.user_id and self.user.role not in STAFF_ROLES:
            raise ValidationError(
                {'user': 'A staff profile cannot belong to a user with the Patient role.'}
            )
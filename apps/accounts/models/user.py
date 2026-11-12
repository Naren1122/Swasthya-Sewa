import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class Role(models.TextChoices):
    """
    Role definitions adhering strictly to MediCore PRD §3.
    Enforces least privilege and role-based permissions across hospital workspaces.
    """
    ADMIN = 'ADMIN', 'Hospital Administrator'
    RECEPTIONIST = 'RECEPTIONIST', 'Receptionist / Front Desk'
    DOCTOR = 'DOCTOR', 'Doctor'
    NURSE = 'NURSE', 'Nurse / Clinical Staff'
    LAB_TECHNICIAN = 'LAB_TECHNICIAN', 'Laboratory Technician'
    PHARMACIST = 'PHARMACIST', 'Pharmacist'
    BILLING = 'BILLING', 'Billing Staff'
    PATIENT = 'PATIENT', 'Patient'


# Every role except PATIENT is hospital staff. Single source of truth for
# permissions and StaffProfile validation.
STAFF_ROLES = frozenset(role for role in Role if role != Role.PATIENT)
class UserManager(BaseUserManager):
    """
    Custom manager for MediCore's User model where email is the primary login credential.
    """

    def get_by_natural_key(self, username):
        # Case-insensitive so "Admin@X.com" can log in to /admin/ as well.
        return self.get(email__iexact=username)
 
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('An email address is required.')
        extra_fields.setdefault('is_active', True)
        # The email is normalized (stripped + lowercased) in User.save().
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user
 
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', Role.ADMIN)
 
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
 
        return self.create_user(email, password, **extra_fields)
 
 
class User(AbstractBaseUser, PermissionsMixin):
    """
    Core authentication entity for MediCore.
 
    - UUIDv4 primary key, so IDs are not sequential or guessable. Object-level
      permission checks are still required (see permissions.IsSelfOrAdmin).
    - Email is the unique, case-insensitive login credential.
    - `role` drives role-based access control.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=255)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, blank=True)
    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.PATIENT,
        db_index=True,
    )
 
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
 
    objects = UserManager()
 
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
 
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
        constraints = [
            models.UniqueConstraint(
                Lower('email'),
                name='unique_user_email_case_insensitive',
            ),
        ]
 
    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        # Administrators must be able to reach the Django admin site.
        if self.role == Role.ADMIN:
            self.is_staff = True
        super().save(*args, **kwargs)
 
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
 
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email
 
    @property
    def is_admin(self):
        return self.role == Role.ADMIN or self.is_superuser
 
    @property
    def is_doctor(self):
        return self.role == Role.DOCTOR
 
    @property
    def is_receptionist(self):
        return self.role == Role.RECEPTIONIST
 
    @property
    def is_patient(self):
        return self.role == Role.PATIENT
 
    @property
    def is_nurse(self):
        return self.role == Role.NURSE
 
    @property
    def is_lab_technician(self):
        return self.role == Role.LAB_TECHNICIAN
 
    @property
    def is_pharmacist(self):
        return self.role == Role.PHARMACIST
 
    @property
    def is_billing(self):
        return self.role == Role.BILLING
 
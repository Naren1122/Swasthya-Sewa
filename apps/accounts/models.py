import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from apps.core.models import BaseModel

class CustomUserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email, password=None, full_name='', role='PATIENT', **extra_fields):
        if not email:
            raise ValueError('An email address is required.')
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            full_name=full_name,
            role=role,
            username=email,  # Keeps Django internals happy while using email
            **extra_fields
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, full_name='Administrator', **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, full_name=full_name, **extra_fields)


class User(AbstractUser, BaseModel):
    """
    Custom User model with UUIDv4 primary key and 3 strict roles:
    - PATIENT: Can self-register (Email/Password or Google).
    - DOCTOR: Provisioned by Admin only.
    - ADMIN: Platform/Hospital administrator.
    """
    class Role(models.TextChoices):
        PATIENT = 'PATIENT', 'Patient'
        DOCTOR = 'DOCTOR', 'Doctor'
        ADMIN = 'ADMIN', 'Admin'

    # Authentication & Personal Information
    email = models.EmailField('Email Address', unique=True, db_index=True)
    full_name = models.CharField('Full Name', max_length=150)
    phone = models.CharField('Phone Number', max_length=20, blank=True, null=True)
    role = models.CharField('Role', max_length=20, choices=Role.choices, default=Role.PATIENT)

    # Use email for login instead of username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()}) - {self.email}"

    def save(self, *args, **kwargs):
        # Automatically sync username with email to prevent duplicate empty username violations
        if not self.username and self.email:
            self.username = self.email
        elif self.email and self.username != self.email:
            self.username = self.email
        super().save(*args, **kwargs)

    @property
    def is_doctor(self) -> bool:
        return self.role == self.Role.DOCTOR

    @property
    def is_patient(self) -> bool:
        return self.role == self.Role.PATIENT

    @property
    def is_admin_user(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser

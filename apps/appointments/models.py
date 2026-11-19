import uuid
from datetime import timedelta
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.core.models import BaseModel
from apps.doctors.models import DoctorProfile

class Appointment(BaseModel):
    """
    Appointment Booking & Teleconsultation Record.
    Tracks reservation lifecycle, 10-minute atomic hold windows,
    payment validation states, and video room assignments.
    """
    class ConsultationType(models.TextChoices):
        PHYSICAL = 'PHYSICAL', 'Hospital Clinic Visit'
        TELEMEDICINE = 'TELEMEDICINE', 'HD Video Consultation'

    class Status(models.TextChoices):
        PENDING_PAYMENT = 'PENDING_PAYMENT', 'Pending Payment'
        PENDING = 'PENDING', 'Pending Approval'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        REJECTED = 'REJECTED', 'Rejected'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        EXPIRED = 'EXPIRED', 'Expired'

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments',
        help_text="User booking the consultation"
    )
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='appointments',
        help_text="Doctor conducting the consultation"
    )
    appointment_date = models.DateField(
        'Appointment Date',
        db_index=True
    )
    start_time = models.TimeField('Start Time')
    end_time = models.TimeField('End Time')
    consultation_type = models.CharField(
        'Consultation Mode',
        max_length=20,
        choices=ConsultationType.choices,
        default=ConsultationType.PHYSICAL
    )
    status = models.CharField(
        'Appointment Status',
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
        db_index=True
    )
    telemed_room_id = models.CharField(
        'Jitsi Video Room ID',
        max_length=120,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Encrypted, unique room identifier for in-browser teleconsultation"
    )
    expires_at = models.DateTimeField(
        'Hold Expiration Timestamp',
        db_index=True,
        help_text="10-minute payment countdown window for temporary slot hold"
    )
    patient_notes = models.TextField(
        'Symptoms / Reason for Visit',
        blank=True,
        help_text="Optional patient pre-consultation notes or symptoms"
    )

    class Meta:
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
        ordering = ['-appointment_date', '-start_time']
        indexes = [
            models.Index(fields=['doctor', 'appointment_date', 'status']),
            models.Index(fields=['patient', 'status']),
        ]

    def __str__(self):
        return f"{self.patient.full_name} with {self.doctor.user.full_name} on {self.appointment_date} ({self.start_time.strftime('%H:%M')}) - {self.get_status_display()}"

    def clean(self):
        super().clean()
        # 1. Option 1 Guard: Self-Booking Prevention
        if self.patient_id and self.doctor_id and self.doctor.user_id == self.patient_id:
            raise ValidationError("A doctor cannot book an appointment with themselves.")

        # 2. Start time must precede end time
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Appointment start time must be earlier than end time.")

    @property
    def is_hold_active(self) -> bool:
        """Returns True if this appointment is in its 10-minute payment hold window."""
        return self.status == self.Status.PENDING_PAYMENT and self.expires_at > timezone.now()

    @property
    def has_hold_expired(self) -> bool:
        """Returns True if the 10-minute hold window lapsed without payment."""
        return self.status == self.Status.PENDING_PAYMENT and self.expires_at <= timezone.now()

    @property
    def fee(self):
        """Calculates applicable fee based on consultation mode."""
        if self.consultation_type == self.ConsultationType.TELEMEDICINE:
            return self.doctor.fee_video
        return self.doctor.fee_physical

    def generate_telemed_room_id(self):
        """Generates a secure, unguessable room slug for Jitsi Meet."""
        if not self.telemed_room_id:
            self.telemed_room_id = f"swasthya-{uuid.uuid4().hex[:16]}"

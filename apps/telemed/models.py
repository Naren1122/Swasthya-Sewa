import os
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import BaseModel

class MedicalDocument(BaseModel):
    """
    Patient-uploaded diagnostic reports and clinical files associated with an appointment.
    Stored on Cloudinary or local media.
    """
    class DocumentType(models.TextChoices):
        LAB_REPORT = 'LAB_REPORT', 'Lab / Blood Test Report'
        PRESCRIPTION = 'PRESCRIPTION', 'Previous Prescription'
        IMAGING = 'IMAGING', 'X-Ray / CT / Ultrasound Imaging'
        DISCHARGE_SUMMARY = 'DISCHARGE_SUMMARY', 'Discharge Summary'
        OTHER = 'OTHER', 'Other Medical Document'

    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        related_name='medical_documents',
        help_text="Consultation appointment associated with this document"
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_medical_documents',
        help_text="Patient who uploaded this medical document"
    )
    document_type = models.CharField(
        'Document Category',
        max_length=30,
        choices=DocumentType.choices,
        default=DocumentType.LAB_REPORT
    )
    title = models.CharField(
        'Document Title / Description',
        max_length=150,
        help_text="e.g. Complete Blood Count (CBC), Chest X-Ray"
    )
    file = models.FileField(
        'Document File',
        upload_to='medical_docs/%Y/%m/',
        help_text="Uploaded PDF, JPG, PNG, or WEBP file"
    )
    file_size_bytes = models.PositiveIntegerField(
        'File Size in Bytes',
        null=True,
        blank=True
    )
    notes = models.TextField(
        'Patient Notes / Context',
        blank=True,
        default=''
    )

    class Meta:
        verbose_name = 'Medical Document'
        verbose_name_plural = 'Medical Documents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_document_type_display()}) - {self.patient.full_name}"

    @property
    def extension(self) -> str:
        if self.file and self.file.name:
            return os.path.splitext(self.file.name)[1].lower()
        return ''

    @property
    def is_image(self) -> bool:
        return self.extension in ['.jpg', '.jpeg', '.png', '.webp']

    @property
    def is_pdf(self) -> bool:
        return self.extension == '.pdf'


class ConsultationNote(BaseModel):
    """
    Doctor's clinical notes, diagnosis, prescriptions, and follow-up guidance
    recorded during or immediately after the teleconsultation.
    """
    appointment = models.OneToOneField(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        related_name='consultation_note',
        help_text="Consultation session for which this note was recorded"
    )
    doctor = models.ForeignKey(
        'doctors.DoctorProfile',
        on_delete=models.CASCADE,
        related_name='consultation_notes',
        help_text="Doctor authoring this clinical record"
    )
    diagnosis = models.TextField(
        'Clinical Diagnosis / Impression',
        blank=True,
        default='',
        help_text="Primary medical diagnosis identified during consultation"
    )
    symptoms = models.TextField(
        'Presenting Symptoms',
        blank=True,
        default='',
        help_text="Symptoms observed or reported by patient"
    )
    prescription = models.TextField(
        'Medications & Dosages',
        blank=True,
        default='',
        help_text="List of medications, dosage schedule, and instructions"
    )
    advice = models.TextField(
        'Dietary & Lifestyle Advice',
        blank=True,
        default='',
        help_text="General lifestyle, dietary, or precaution instructions"
    )
    follow_up_date = models.DateField(
        'Suggested Follow-Up Date',
        null=True,
        blank=True
    )
    prescription_file = models.FileField(
        'Official Prescription Document',
        upload_to='prescriptions/%Y/%m/',
        null=True,
        blank=True,
        help_text="Optional scanned or digital signed prescription slip"
    )
    is_finalized = models.BooleanField(
        'Is Finalized',
        default=False,
        help_text="Finalized notes cannot be altered without an audit trail"
    )
    finalized_at = models.DateTimeField(
        'Finalized Timestamp',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Consultation Note'
        verbose_name_plural = 'Consultation Notes'
        ordering = ['-created_at']

    def __str__(self):
        return f"Clinical Note for Appt #{str(self.appointment_id)[:8]} by {self.doctor.user.full_name}"

    def finalize(self):
        """Finalizes the clinical note and records timestamp."""
        self.is_finalized = True
        self.finalized_at = timezone.now()
        self.save()

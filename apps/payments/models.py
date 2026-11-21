import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import BaseModel

class Payment(BaseModel):
    class Gateway(models.TextChoices):
        ESEWA = 'ESEWA', 'eSewa Mobile Wallet'
        KHALTI = 'KHALTI', 'Khalti Digital Wallet'
        CASH_ON_ARRIVAL = 'CASH_ON_ARRIVAL', 'Pay at Hospital Counter'

    class Status(models.TextChoices):
        INITIATED = 'INITIATED', 'Initiated'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        related_name='payments',
        help_text="Consultation appointment associated with this payment"
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments',
        help_text="Patient making the payment"
    )
    gateway = models.CharField(
        'Payment Gateway',
        max_length=30,
        choices=Gateway.choices
    )
    transaction_uuid = models.UUIDField(
        'Transaction UUID',
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        help_text="Internal unique transaction reference passed to gateway"
    )
    gateway_ref = models.CharField(
        'Gateway Reference / PIDX',
        max_length=200,
        blank=True,
        null=True,
        db_index=True,
        help_text="Gateway-assigned reference: eSewa ref_id or Khalti pidx"
    )
    amount = models.DecimalField(
        'Payment Amount (NPR)',
        max_digits=10,
        decimal_places=2,
        help_text="Total transaction amount in Nepalese Rupees"
    )
    status = models.CharField(
        'Payment Status',
        max_length=20,
        choices=Status.choices,
        default=Status.INITIATED,
        db_index=True
    )
    gateway_response = models.JSONField(
        'Raw Gateway Response',
        default=dict,
        blank=True,
        help_text="Complete audit payload returned by gateway verification"
    )
    initiated_at = models.DateTimeField(
        'Initiated Timestamp',
        default=timezone.now
    )
    completed_at = models.DateTimeField(
        'Completed Timestamp',
        null=True,
        blank=True
    )
    refunded_at = models.DateTimeField(
        'Refunded Timestamp',
        null=True,
        blank=True
    )
    refund_reason = models.CharField(
        'Refund Reason',
        max_length=255,
        blank=True,
        default=''
    )

    class Meta:
        verbose_name = 'Payment Transaction'
        verbose_name_plural = 'Payment Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['appointment', 'status']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['gateway', 'status']),
        ]

    def __str__(self):
        return f"{self.gateway} - NPR {self.amount} ({self.get_status_display()}) for Appt #{str(self.appointment_id)[:8]}"

    def mark_success(self, gateway_ref: str, response_data: dict = None):
        """Marks transaction as successful and timestamps it."""
        self.status = self.Status.SUCCESS
        self.gateway_ref = gateway_ref
        if response_data:
            self.gateway_response = response_data
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'gateway_ref', 'gateway_response', 'completed_at', 'updated_at'])

    def mark_failed(self, response_data: dict = None):
        """Marks transaction as failed."""
        self.status = self.Status.FAILED
        if response_data:
            self.gateway_response = response_data
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'gateway_response', 'completed_at', 'updated_at'])

    def mark_refunded(self, reason: str = '', response_data: dict = None):
        """Marks transaction as refunded and records timestamp and reason."""
        self.status = self.Status.REFUNDED
        self.refund_reason = reason
        self.refunded_at = timezone.now()
        if response_data:
            if not isinstance(self.gateway_response, dict):
                self.gateway_response = {}
            self.gateway_response['refund_response'] = response_data
        self.save(update_fields=['status', 'refund_reason', 'refunded_at', 'gateway_response', 'updated_at'])

import uuid
from rest_framework import serializers
from apps.appointments.models import Appointment

class AppointmentSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for appointment consultation records.
    """
    patient_id = serializers.UUIDField(source='patient.id', read_only=True)
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_id = serializers.UUIDField(source='doctor.id', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.full_name', read_only=True)
    department_name = serializers.CharField(source='doctor.department.name', read_only=True)
    fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_hold_active = serializers.BooleanField(read_only=True)
    has_hold_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient_id',
            'patient_name',
            'doctor_id',
            'doctor_name',
            'department_name',
            'appointment_date',
            'start_time',
            'end_time',
            'consultation_type',
            'fee',
            'status',
            'telemed_room_id',
            'expires_at',
            'is_hold_active',
            'has_hold_expired',
            'patient_notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class AppointmentHoldRequestSerializer(serializers.Serializer):
    """
    Input serializer for placing an atomic 10-minute hold on a doctor's slot.
    """
    doctor_id = serializers.UUIDField(required=True, help_text="UUID of the doctor profile")
    date = serializers.DateField(required=True, help_text="Date of consultation (YYYY-MM-DD)")
    time = serializers.TimeField(required=True, help_text="Slot start time (HH:MM or HH:MM:SS)")
    consultation_type = serializers.ChoiceField(
        choices=Appointment.ConsultationType.choices,
        default=Appointment.ConsultationType.PHYSICAL,
        help_text="Mode of consultation (PHYSICAL or TELEMEDICINE)"
    )
    patient_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Pre-consultation symptoms or visit reason (optional)"
    )


class AppointmentConfirmRequestSerializer(serializers.Serializer):
    """
    Input serializer for confirming an active 10-minute hold.
    """
    consultation_type = serializers.ChoiceField(
        choices=Appointment.ConsultationType.choices,
        required=False,
        help_text="Updated consultation mode (optional)"
    )
    patient_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Updated symptoms or visit reason (optional)"
    )


class AppointmentCancelRequestSerializer(serializers.Serializer):
    """
    Input serializer for cancelling an appointment.
    """
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=300,
        help_text="Reason for cancellation (optional)"
    )

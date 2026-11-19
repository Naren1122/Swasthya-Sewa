from rest_framework import serializers
from apps.payments.models import Payment
from apps.appointments.models import Appointment

class PaymentSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Payment ledger transactions.
    """
    appointment_id = serializers.UUIDField(source='appointment.id', read_only=True)
    doctor_name = serializers.CharField(source='appointment.doctor.user.full_name', read_only=True)
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    gateway_display = serializers.CharField(source='get_gateway_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id',
            'appointment_id',
            'doctor_name',
            'patient_name',
            'gateway',
            'gateway_display',
            'amount',
            'status',
            'status_display',
            'transaction_uuid',
            'gateway_ref',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class PaymentInitiateRequestSerializer(serializers.Serializer):
    """
    Input serializer for initiating payment on an active appointment hold.
    """
    appointment_id = serializers.UUIDField(
        required=True,
        help_text="UUID of the appointment currently on active 10-minute hold"
    )
    gateway = serializers.ChoiceField(
        choices=Payment.Gateway.choices,
        required=True,
        help_text="Gateway choice: ESEWA, KHALTI, or CASH_ON_ARRIVAL"
    )
    return_url = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text="Custom redirect return URL for mobile/SPA clients"
    )
    failure_url = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text="Custom failure redirect URL for eSewa"
    )


class PaymentVerifyRequestSerializer(serializers.Serializer):
    """
    Input serializer for verifying eSewa or Khalti payment callbacks.
    """
    gateway = serializers.ChoiceField(
        choices=[(Payment.Gateway.ESEWA, 'eSewa'), (Payment.Gateway.KHALTI, 'Khalti')],
        required=True,
        help_text="Gateway used for payment: ESEWA or KHALTI"
    )
    # eSewa parameter: Base64-encoded callback string
    data = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="eSewa Base64-encoded callback payload"
    )
    # Khalti parameter: transaction lookup token
    pidx = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Khalti lookup token (pidx)"
    )

    def validate(self, attrs):
        gateway = attrs.get('gateway')
        if gateway == Payment.Gateway.ESEWA and not attrs.get('data'):
            raise serializers.ValidationError({"data": "The 'data' parameter is required for eSewa verification."})
        if gateway == Payment.Gateway.KHALTI and not attrs.get('pidx'):
            raise serializers.ValidationError({"pidx": "The 'pidx' parameter is required for Khalti verification."})
        return attrs

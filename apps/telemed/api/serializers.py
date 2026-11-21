from rest_framework import serializers
from apps.telemed.models import MedicalDocument, ConsultationNote

class MedicalDocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for diagnostic reports and medical document uploads.
    """
    appointment_id = serializers.UUIDField(source='appointment.id', read_only=True)
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    is_image = serializers.BooleanField(read_only=True)
    is_pdf = serializers.BooleanField(read_only=True)

    class Meta:
        model = MedicalDocument
        fields = [
            'id',
            'appointment_id',
            'patient_name',
            'document_type',
            'document_type_display',
            'title',
            'file',
            'file_size_bytes',
            'notes',
            'is_image',
            'is_pdf',
            'created_at',
        ]
        read_only_fields = ['id', 'appointment_id', 'patient_name', 'created_at']


class ConsultationNoteSerializer(serializers.ModelSerializer):
    """
    Serializer for doctor's clinical notes, diagnosis, and prescriptions.
    """
    appointment_id = serializers.UUIDField(source='appointment.id', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.full_name', read_only=True)
    department_name = serializers.CharField(source='doctor.department.name', read_only=True)

    class Meta:
        model = ConsultationNote
        fields = [
            'id',
            'appointment_id',
            'doctor_name',
            'department_name',
            'diagnosis',
            'symptoms',
            'prescription',
            'advice',
            'follow_up_date',
            'prescription_file',
            'is_finalized',
            'finalized_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'appointment_id', 'doctor_name', 'department_name', 'created_at', 'updated_at']


class TelemedRoomAccessResponseSerializer(serializers.Serializer):
    """
    Response schema for teleconsultation room authentication & authorization.
    """
    room_name = serializers.CharField()
    user_role = serializers.CharField()
    display_name = serializers.CharField()
    user_email = serializers.EmailField()
    doctor_name = serializers.CharField()
    patient_name = serializers.CharField()
    department_name = serializers.CharField()
    scheduled_time = serializers.CharField()
    is_doctor = serializers.BooleanField()
    is_patient = serializers.BooleanField()

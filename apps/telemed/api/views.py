from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.appointments.models import Appointment
from apps.appointments.services.booking_service import complete_appointment
from apps.telemed.models import MedicalDocument, ConsultationNote
from apps.telemed.services.room_service import TelemedRoomService
from apps.telemed.api.serializers import (
    MedicalDocumentSerializer,
    ConsultationNoteSerializer,
    TelemedRoomAccessResponseSerializer,
)

@extend_schema(
    tags=['Telemedicine'],
    summary="Verify teleconsultation room access & get participant credentials",
    description="Validates cryptographic room access, timing window, and role permissions for the video session.",
    responses={
        200: TelemedRoomAccessResponseSerializer,
        403: OpenApiResponse(description="Access denied or outside allowed consultation time window"),
        404: OpenApiResponse(description="Appointment not found"),
    }
)
class TelemedRoomAccessAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, appointment_id, *args, **kwargs):
        is_authorized, err_msg, appointment, context = TelemedRoomService.verify_telemed_access(
            user=request.user,
            appointment_id=appointment_id
        )

        if not is_authorized:
            return Response({'detail': err_msg}, status=status.HTTP_403_FORBIDDEN)

        serializer = TelemedRoomAccessResponseSerializer(context)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Telemedicine'],
    summary="List or upload medical reports for an appointment",
    description="Allows patients and assigned doctors to upload and view clinical files (PDF, JPG, PNG).",
    responses={
        200: MedicalDocumentSerializer(many=True),
        201: MedicalDocumentSerializer,
    }
)
class MedicalDocumentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_appointment(self, user, appointment_id):
        appointment = Appointment.objects.select_related('doctor__user', 'patient').filter(id=appointment_id).first()
        if not appointment:
            return None
        if user.id not in [appointment.patient.id, appointment.doctor.user.id]:
            return None
        return appointment

    def get(self, request, appointment_id, *args, **kwargs):
        appointment = self.get_appointment(request.user, appointment_id)
        if not appointment:
            return Response({'detail': "Appointment not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

        docs = appointment.medical_documents.all().order_by('-created_at')
        serializer = MedicalDocumentSerializer(docs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, appointment_id, *args, **kwargs):
        appointment = self.get_appointment(request.user, appointment_id)
        if not appointment:
            return Response({'detail': "Appointment not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({'detail': "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        if uploaded_file.size > 10 * 1024 * 1024:
            return Response({'detail': "File exceeds 10 MB limit."}, status=status.HTTP_400_BAD_REQUEST)

        title = request.data.get('title', '').strip() or uploaded_file.name
        doc_type = request.data.get('document_type', MedicalDocument.DocumentType.LAB_REPORT)
        notes = request.data.get('notes', '').strip()

        doc = MedicalDocument.objects.create(
            appointment=appointment,
            patient=appointment.patient,
            title=title,
            document_type=doc_type,
            file=uploaded_file,
            file_size_bytes=uploaded_file.size,
            notes=notes
        )

        serializer = MedicalDocumentSerializer(doc)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Telemedicine'],
    summary="Get or record clinical consultation notes & prescription",
    description="Doctor-only endpoint to write clinical diagnosis, prescriptions, and advice. Can mark appointment COMPLETED.",
    responses={
        200: ConsultationNoteSerializer,
        403: OpenApiResponse(description="Forbidden: Only assigned doctor can author notes"),
    }
)
class ConsultationNoteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, appointment_id, *args, **kwargs):
        appointment = Appointment.objects.select_related('doctor__user', 'patient').filter(id=appointment_id).first()
        if not appointment or request.user.id not in [appointment.patient.id, appointment.doctor.user.id]:
            return Response({'detail': "Appointment not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

        note = getattr(appointment, 'consultation_note', None)
        if not note:
            return Response({'detail': "No clinical notes recorded yet."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ConsultationNoteSerializer(note)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, appointment_id, *args, **kwargs):
        appointment = Appointment.objects.select_related('doctor__user', 'patient').filter(id=appointment_id).first()
        if not appointment:
            return Response({'detail': "Appointment not found."}, status=status.HTTP_404_NOT_FOUND)

        if request.user.id != appointment.doctor.user.id:
            return Response({'detail': "Only the assigned doctor can record clinical notes."}, status=status.HTTP_403_FORBIDDEN)

        note, _ = ConsultationNote.objects.get_or_create(
            appointment=appointment,
            defaults={'doctor': appointment.doctor}
        )

        note.diagnosis = request.data.get('diagnosis', note.diagnosis).strip()
        note.symptoms = request.data.get('symptoms', note.symptoms).strip()
        note.prescription = request.data.get('prescription', note.prescription).strip()
        note.advice = request.data.get('advice', note.advice).strip()
        
        follow_up = request.data.get('follow_up_date')
        if follow_up:
            note.follow_up_date = follow_up

        prescription_file = request.FILES.get('prescription_file')
        if prescription_file:
            note.prescription_file = prescription_file

        if request.data.get('finalize') in [True, 'true', 'True', 1, '1']:
            note.finalize()
            if appointment.status in [Appointment.Status.ACCEPTED, Appointment.Status.CONFIRMED]:
                complete_appointment(doctor_user=request.user, appointment_id=appointment.id)
        else:
            note.save()

        serializer = ConsultationNoteSerializer(note)
        return Response(serializer.data, status=status.HTTP_200_OK)

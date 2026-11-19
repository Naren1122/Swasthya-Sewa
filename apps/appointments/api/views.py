import uuid
from django.db.models import Q
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from apps.appointments.models import Appointment
from apps.appointments.api.serializers import (
    AppointmentSerializer,
    AppointmentHoldRequestSerializer,
    AppointmentConfirmRequestSerializer,
    AppointmentCancelRequestSerializer,
)
from apps.appointments.services.booking_service import (
    hold_appointment_slot,
    confirm_appointment_booking,
    cancel_appointment_hold,
    cancel_confirmed_appointment,
)
from apps.appointments.exceptions import (
    SlotUnavailableError,
    SelfBookingError,
    DoctorUnavailableError,
    BookingError,
)

@extend_schema(
    tags=['Appointments'],
    summary="Hold an appointment slot (10-minute hold lock)",
    description="Places a concurrency-safe 10-minute hold lock on a doctor consultation slot. Uses PostgreSQL row-locking to prevent race conditions.",
    request=AppointmentHoldRequestSerializer,
    responses={
        201: AppointmentSerializer,
        400: OpenApiResponse(description="Validation error or self-booking attempt"),
        409: OpenApiResponse(description="Slot already occupied or just claimed by another user"),
    }
)
class AppointmentHoldAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AppointmentHoldRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.cleaned_data if hasattr(serializer, 'cleaned_data') else serializer.validated_data

        try:
            appointment = hold_appointment_slot(
                patient=request.user,
                doctor_id=data['doctor_id'],
                target_date=data['date'],
                start_time=data['time'],
                consultation_type=data.get('consultation_type', Appointment.ConsultationType.PHYSICAL),
                patient_notes=data.get('patient_notes', '')
            )
        except SelfBookingError as err:
            return Response({'detail': str(err)}, status=status.HTTP_400_BAD_REQUEST)
        except SlotUnavailableError as err:
            return Response({'detail': str(err)}, status=status.HTTP_409_CONFLICT)
        except (DoctorUnavailableError, BookingError) as err:
            return Response({'detail': str(err)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Appointments'],
    summary="Confirm an active slot hold",
    description="Transitions an appointment from PENDING_PAYMENT to CONFIRMED. Validates hold expiration and assigns a Jitsi telemed room ID if video call.",
    request=AppointmentConfirmRequestSerializer,
    responses={
        200: AppointmentSerializer,
        400: OpenApiResponse(description="Hold expired, invalid state, or validation error"),
        409: OpenApiResponse(description="Slot conflict"),
    }
)
class AppointmentConfirmAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, appointment_id, *args, **kwargs):
        serializer = AppointmentConfirmRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            appointment = confirm_appointment_booking(
                user=request.user,
                appointment_id=appointment_id,
                consultation_type=data.get('consultation_type'),
                patient_notes=data.get('patient_notes', '')
            )
        except SlotUnavailableError as err:
            return Response({'detail': str(err)}, status=status.HTTP_409_CONFLICT)
        except (DoctorUnavailableError, BookingError) as err:
            return Response({'detail': str(err)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Appointments'],
    summary="Cancel / release a 10-minute hold",
    description="Releases a temporary slot hold and returns the slot immediately to the available pool.",
    responses={
        200: OpenApiResponse(description="Slot hold released successfully"),
        400: OpenApiResponse(description="Unable to release hold or slot already expired"),
    }
)
class AppointmentCancelHoldAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, appointment_id, *args, **kwargs):
        success = cancel_appointment_hold(user=request.user, appointment_id=appointment_id)
        if not success:
            return Response(
                {'detail': 'Unable to release hold. The slot may have already expired or does not belong to you.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response({'detail': 'Slot hold released successfully.'}, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Appointments'],
    summary="Cancel a confirmed appointment",
    description="Cancels an appointment (callable by patient or assigned doctor) with an optional reason.",
    request=AppointmentCancelRequestSerializer,
    responses={
        200: AppointmentSerializer,
        400: OpenApiResponse(description="Cannot cancel or unauthorized"),
    }
)
class AppointmentCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, appointment_id, *args, **kwargs):
        serializer = AppointmentCancelRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason', '')

        try:
            appointment = cancel_confirmed_appointment(
                user=request.user,
                appointment_id=appointment_id,
                cancellation_reason=reason
            )
        except BookingError as err:
            return Response({'detail': str(err)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Appointments'],
    summary="List patient's booked consultations",
    description="Returns all current and past appointments for the authenticated user, ordered chronologically descending.",
    parameters=[
        OpenApiParameter(name='status', description='Filter by status (e.g. CONFIRMED, PENDING_PAYMENT, CANCELLED)', required=False, type=str),
    ],
    responses={200: AppointmentSerializer(many=True)}
)
class PatientAppointmentListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = Appointment.objects.select_related(
            'doctor', 'doctor__user', 'doctor__department', 'patient'
        ).filter(patient=request.user).order_by('-appointment_date', '-start_time')

        status_param = request.query_params.get('status')
        if status_param and status_param.upper() in Appointment.Status.values:
            queryset = queryset.filter(status=status_param.upper())

        serializer = AppointmentSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Appointments'],
    summary="Retrieve appointment details / receipt",
    description="Retrieves appointment record and receipt details. Accessible only to the booking patient or the assigned doctor.",
    responses={
        200: AppointmentSerializer,
        404: OpenApiResponse(description="Appointment not found or unauthorized"),
    }
)
class AppointmentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, appointment_id, *args, **kwargs):
        appointment = Appointment.objects.select_related(
            'doctor', 'doctor__user', 'doctor__department', 'patient'
        ).filter(
            Q(patient=request.user) | Q(doctor__user=request.user),
            id=appointment_id
        ).first()

        if not appointment:
            return Response({'detail': 'Appointment not found or access denied.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_200_OK)

import logging
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.payments.models import Payment
from apps.appointments.models import Appointment
from apps.appointments.services.booking_service import confirm_appointment_booking
from apps.payments.services.esewa_service import EsewaPaymentService
from apps.payments.services.khalti_service import KhaltiPaymentService
from apps.payments.api.serializers import (
    PaymentSerializer,
    PaymentInitiateRequestSerializer,
    PaymentVerifyRequestSerializer,
)

logger = logging.getLogger(__name__)

@extend_schema(
    tags=['Payments'],
    summary="Initiate payment for an appointment hold",
    description="Initiates eSewa ePPS v2, Khalti ePayment v2, or Cash on Arrival for an active appointment hold.",
    request=PaymentInitiateRequestSerializer,
    responses={
        200: OpenApiResponse(description="Payment initiated with gateway redirect/signature details"),
        400: OpenApiResponse(description="Validation error, expired hold, or invalid appointment"),
    }
)
class PaymentInitiateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PaymentInitiateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        appointment = get_object_or_404(
            Appointment.objects.select_related('doctor__user', 'doctor__department'),
            id=data['appointment_id'],
            patient=request.user
        )

        if not appointment.is_hold_active:
            return Response(
                {'detail': "Appointment hold has expired or is no longer in pending payment status."},
                status=status.HTTP_400_BAD_REQUEST
            )

        gateway = data['gateway']
        amount = appointment.fee

        # 1. Cash on Arrival (Pay at Desk)
        if gateway == Payment.Gateway.CASH_ON_ARRIVAL:
            payment = Payment.objects.create(
                appointment=appointment,
                patient=request.user,
                gateway=Payment.Gateway.CASH_ON_ARRIVAL,
                amount=amount,
                status=Payment.Status.INITIATED,
            )
            confirm_appointment_booking(
                user=request.user,
                appointment_id=appointment.id,
                consultation_type=appointment.consultation_type,
                patient_notes=appointment.patient_notes
            )
            return Response({
                'gateway': Payment.Gateway.CASH_ON_ARRIVAL,
                'status': 'CONFIRMED',
                'message': "Cash on Arrival selected. Appointment submitted to doctor queue.",
                'payment': PaymentSerializer(payment).data,
            }, status=status.HTTP_200_OK)

        # 2. eSewa ePPS (v2)
        elif gateway == Payment.Gateway.ESEWA:
            payment = Payment.objects.create(
                appointment=appointment,
                patient=request.user,
                gateway=Payment.Gateway.ESEWA,
                amount=amount,
                status=Payment.Status.INITIATED,
            )
            base_url = request.build_absolute_uri('/')[:-1]
            success_url = data.get('return_url') or f"{base_url}{reverse('esewa_success')}"
            failure_url = data.get('failure_url') or f"{base_url}{reverse('esewa_failure')}?uuid={payment.transaction_uuid}"

            esewa_payload = EsewaPaymentService.initiate_payment(
                payment=payment,
                success_url=success_url,
                failure_url=failure_url
            )
            return Response({
                'gateway': Payment.Gateway.ESEWA,
                'status': 'INITIATED',
                'action_url': esewa_payload['action_url'],
                'fields': esewa_payload['fields'],
                'payment': PaymentSerializer(payment).data,
            }, status=status.HTTP_200_OK)

        # 3. Khalti ePayment (v2)
        elif gateway == Payment.Gateway.KHALTI:
            payment = Payment.objects.create(
                appointment=appointment,
                patient=request.user,
                gateway=Payment.Gateway.KHALTI,
                amount=amount,
                status=Payment.Status.INITIATED,
            )
            base_url = request.build_absolute_uri('/')[:-1]
            return_url = data.get('return_url') or f"{base_url}{reverse('khalti_callback')}"

            result = KhaltiPaymentService.initiate_payment(
                payment=payment,
                return_url=return_url,
                website_url=base_url
            )

            if result.get('success') and 'payment_url' in result:
                return Response({
                    'gateway': Payment.Gateway.KHALTI,
                    'status': 'INITIATED',
                    'payment_url': result['payment_url'],
                    'pidx': result['pidx'],
                    'payment': PaymentSerializer(payment).data,
                }, status=status.HTTP_200_OK)
            else:
                payment.mark_failed(response_data=result)
                return Response({
                    'detail': f"Khalti initiation failed: {result.get('error', 'Unknown error')}"
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({'detail': "Invalid payment gateway choice."}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Payments'],
    summary="Verify payment callback from eSewa or Khalti",
    description="Validates cryptographic signature (eSewa) or server-to-server token (Khalti), updates payment ledger, and advances appointment to PENDING.",
    request=PaymentVerifyRequestSerializer,
    responses={
        200: OpenApiResponse(description="Payment verified successfully"),
        400: OpenApiResponse(description="Verification failed or tampered payload"),
    }
)
class PaymentVerifyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PaymentVerifyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        gateway = data['gateway']

        # 1. eSewa Verification
        if gateway == Payment.Gateway.ESEWA:
            encoded_data = data['data']
            is_valid, transaction_uuid, payload = EsewaPaymentService.verify_payment(encoded_data)

            if not is_valid:
                return Response(
                    {'detail': f"eSewa verification failed: {payload.get('error', 'Invalid signature')}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            payment = get_object_or_404(
                Payment.objects.select_related('appointment', 'patient'),
                transaction_uuid=transaction_uuid,
                patient=request.user
            )
            payment.mark_success(gateway_ref=payload.get('transaction_code'), response_data=payload)

            confirm_appointment_booking(
                user=payment.patient,
                appointment_id=payment.appointment.id,
                consultation_type=payment.appointment.consultation_type,
                patient_notes=payment.appointment.patient_notes
            )
            return Response({
                'success': True,
                'message': "Payment verified via eSewa. Appointment submitted for doctor review.",
                'payment': PaymentSerializer(payment).data,
            }, status=status.HTTP_200_OK)

        # 2. Khalti Verification
        elif gateway == Payment.Gateway.KHALTI:
            pidx = data['pidx']
            is_success, status_str, lookup_data = KhaltiPaymentService.verify_payment(pidx)

            payment = Payment.objects.filter(gateway_ref=pidx, patient=request.user).select_related('appointment', 'patient').first()
            if not payment:
                return Response(
                    {'detail': "No matching payment transaction found for this Khalti token."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if not is_success:
                payment.mark_failed(response_data=lookup_data)
                return Response(
                    {'detail': f"Khalti payment verification failed ({status_str})."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            payment.mark_success(gateway_ref=pidx, response_data=lookup_data)
            confirm_appointment_booking(
                user=payment.patient,
                appointment_id=payment.appointment.id,
                consultation_type=payment.appointment.consultation_type,
                patient_notes=payment.appointment.patient_notes
            )
            return Response({
                'success': True,
                'message': "Payment verified via Khalti. Appointment submitted for doctor review.",
                'payment': PaymentSerializer(payment).data,
            }, status=status.HTTP_200_OK)

        return Response({'detail': "Invalid gateway."}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Payments'],
    summary="List patient's payment transactions",
    description="Retrieves transaction history and payment receipts for the authenticated user.",
    responses={200: PaymentSerializer(many=True)}
)
class PaymentListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        payments = Payment.objects.filter(patient=request.user).select_related('appointment__doctor__user').order_by('-created_at')
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Payments'],
    summary="Get payment details",
    description="Retrieves a single payment transaction by UUID.",
    responses={
        200: PaymentSerializer,
        404: OpenApiResponse(description="Payment not found")
    }
)
class PaymentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, payment_id, *args, **kwargs):
        payment = get_object_or_404(
            Payment.objects.select_related('appointment__doctor__user', 'patient'),
            id=payment_id,
            patient=request.user
        )
        serializer = PaymentSerializer(payment)
        return Response(serializer.data, status=status.HTTP_200_OK)

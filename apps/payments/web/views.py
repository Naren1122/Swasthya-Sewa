import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import timezone
from apps.appointments.models import Appointment
from apps.appointments.services.booking_service import confirm_appointment_booking
from apps.appointments.exceptions import BookingError, SlotUnavailableError
from apps.payments.models import Payment
from apps.payments.services.esewa_service import EsewaPaymentService
from apps.payments.services.khalti_service import KhaltiPaymentService

class PaymentInitiateView(LoginRequiredMixin, View):
    """
    Initiates payment for an appointment in active 10-minute hold.
    Dispatches to eSewa, Khalti, or records Pay-at-Counter option.
    """
    def post(self, request, appointment_id, *args, **kwargs):
        appointment = get_object_or_404(
            Appointment.objects.select_related('doctor', 'doctor__user'),
            id=appointment_id,
            patient=request.user
        )

        if appointment.status != Appointment.Status.PENDING_PAYMENT:
            messages.warning(request, f"Appointment is already in {appointment.get_status_display()} state.")
            return redirect('appointment_detail', appointment_id=appointment.id)

        if appointment.expires_at <= timezone.now():
            appointment.status = Appointment.Status.EXPIRED
            appointment.save(update_fields=['status'])
            messages.error(request, "Your 10-minute slot hold has expired. Please select a new slot.")
            return redirect('doctor_detail', slug=appointment.doctor.slug)

        # Update consultation mode / notes if sent from checkout form
        mode = request.POST.get('consultation_type')
        if mode in Appointment.ConsultationType.values:
            appointment.consultation_type = mode
        notes = request.POST.get('patient_notes')
        if notes:
            appointment.patient_notes = notes.strip()
        appointment.save()

        gateway = request.POST.get('gateway', Payment.Gateway.ESEWA).upper()

        # 1. CASH ON ARRIVAL / PAY AT DESK
        if gateway == Payment.Gateway.CASH_ON_ARRIVAL:
            payment = Payment.objects.create(
                appointment=appointment,
                patient=request.user,
                gateway=Payment.Gateway.CASH_ON_ARRIVAL,
                amount=appointment.fee,
                status=Payment.Status.INITIATED
            )
            confirm_appointment_booking(
                user=request.user,
                appointment_id=appointment.id,
                consultation_type=appointment.consultation_type,
                patient_notes=appointment.patient_notes
            )
            messages.success(request, "Appointment requested! Please pay at the hospital reception counter on arrival.")
            redirect_url = reverse('appointment_detail', kwargs={'appointment_id': appointment.id})
            if request.headers.get('HX-Request'):
                response = HttpResponse(status=200)
                response['HX-Redirect'] = redirect_url
                return response
            return redirect(redirect_url)

        # Create Ledger Record for Gateway Transaction
        payment = Payment.objects.create(
            appointment=appointment,
            patient=request.user,
            gateway=gateway,
            amount=appointment.fee,
            status=Payment.Status.INITIATED
        )

        # 2. eSewa v2 Checkout
        if gateway == Payment.Gateway.ESEWA:
            base_url = request.build_absolute_uri('/')[:-1]
            success_url = f"{base_url}{reverse('esewa_success')}"
            failure_url = f"{base_url}{reverse('esewa_failure')}?uuid={payment.transaction_uuid}"

            esewa_data = EsewaPaymentService.initiate_payment(
                payment=payment,
                success_url=success_url,
                failure_url=failure_url
            )
            return render(request, 'payments/esewa_redirect.html', {
                'action_url': esewa_data['action_url'],
                'fields': esewa_data['fields'],
                'amount': payment.amount,
                'doctor_name': appointment.doctor.user.full_name,
            })

        # 3. Khalti v2 Checkout
        elif gateway == Payment.Gateway.KHALTI:
            base_url = request.build_absolute_uri('/')[:-1]
            return_url = f"{base_url}{reverse('khalti_callback')}"
            website_url = base_url

            result = KhaltiPaymentService.initiate_payment(
                payment=payment,
                return_url=return_url,
                website_url=website_url
            )
            if result.get('success') and 'payment_url' in result:
                return redirect(result['payment_url'])
            else:
                messages.error(request, f"Khalti payment initialization failed: {result.get('error')}")
                return redirect('patient_bookings')

        messages.error(request, "Invalid payment gateway selected.")
        return redirect('doctor_detail', slug=appointment.doctor.slug)


class EsewaSuccessCallbackView(View):
    """
    Verifies eSewa v2 HMAC-SHA256 signature and records transaction success.
    """
    def get(self, request, *args, **kwargs):
        encoded_data = request.GET.get('data')
        if not encoded_data:
            messages.error(request, "Invalid eSewa response payload.")
            return redirect('patient_bookings')

        is_valid, transaction_uuid, data = EsewaPaymentService.verify_payment(encoded_data)

        if not is_valid:
            messages.error(request, f"Payment verification failed: {data.get('error', 'Signature mismatch')}")
            return redirect('patient_bookings')

        payment = get_object_or_404(Payment.objects.select_related('appointment', 'patient'), transaction_uuid=transaction_uuid)
        payment.mark_success(gateway_ref=data.get('transaction_code'), response_data=data)

        # Transition appointment to PENDING (Awaiting doctor acceptance)
        confirm_appointment_booking(
            user=payment.patient,
            appointment_id=payment.appointment.id,
            consultation_type=payment.appointment.consultation_type,
            patient_notes=payment.appointment.patient_notes
        )

        messages.success(request, f"Payment of NPR {payment.amount:.0f} via eSewa verified successfully! Appointment submitted for doctor review.")
        return redirect('appointment_detail', appointment_id=payment.appointment.id)


class EsewaFailureCallbackView(View):
    """
    Handles cancelled or failed eSewa checkout.
    """
    def get(self, request, *args, **kwargs):
        uuid_str = request.GET.get('uuid')
        if uuid_str:
            Payment.objects.filter(transaction_uuid=uuid_str, status=Payment.Status.INITIATED).update(status=Payment.Status.FAILED)

        messages.warning(request, "eSewa payment transaction was cancelled or failed.")
        return redirect('patient_bookings')


class KhaltiCallbackView(View):
    """
    Verifies Khalti v2 payment via server-to-server lookup API.
    """
    def get(self, request, *args, **kwargs):
        pidx = request.GET.get('pidx')
        if not pidx:
            messages.error(request, "Missing Khalti payment identifier (pidx).")
            return redirect('patient_bookings')

        is_success, status_str, data = KhaltiPaymentService.verify_payment(pidx)

        payment = Payment.objects.filter(gateway_ref=pidx).select_related('appointment', 'patient').first()
        if not payment:
            # Fallback to purchase_order_id
            order_id = request.GET.get('purchase_order_id')
            if order_id:
                payment = Payment.objects.filter(transaction_uuid=order_id).select_related('appointment', 'patient').first()

        if not is_success or not payment:
            if payment:
                payment.mark_failed(response_data=data)
            messages.error(request, f"Khalti payment verification failed ({status_str}).")
            return redirect('patient_bookings')

        payment.mark_success(gateway_ref=pidx, response_data=data)

        # Transition appointment to PENDING
        confirm_appointment_booking(
            user=payment.patient,
            appointment_id=payment.appointment.id,
            consultation_type=payment.appointment.consultation_type,
            patient_notes=payment.appointment.patient_notes
        )

        messages.success(request, f"Payment of NPR {payment.amount:.0f} via Khalti verified successfully! Appointment submitted for doctor review.")
        return redirect('appointment_detail', appointment_id=payment.appointment.id)

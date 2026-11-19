import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from apps.accounts.web.decorators import doctor_required
from apps.appointments.models import Appointment
from apps.appointments.web.forms import AppointmentHoldForm, AppointmentConfirmForm
from apps.appointments.services.booking_service import (
    hold_appointment_slot,
    cancel_appointment_hold,
    confirm_appointment_booking,
    accept_appointment,
    reject_appointment,
    complete_appointment,
    cancel_confirmed_appointment,
)
from apps.appointments.exceptions import (
    SlotUnavailableError,
    SelfBookingError,
    DoctorUnavailableError,
    BookingError,
)

class AppointmentHoldView(View):
    """
    Handles atomic 10-minute appointment slot hold requests.
    Supports both HTMX modal swaps and standard POST redirects.
    """
    def post(self, request, *args, **kwargs):
        # 1. Unauthenticated Interception (Frictionless redirect to Login)
        if not request.user.is_authenticated:
            if request.headers.get('HX-Request'):
                # Tell HTMX to cleanly redirect the full browser window to login
                response = HttpResponse(status=401)
                login_url = f"/accounts/login/?next={request.META.get('HTTP_REFERER', '/')}"
                response['HX-Redirect'] = login_url
                return response
            return redirect('login')

        form = AppointmentHoldForm(request.POST)
        if not form.is_valid():
            err_msg = next(iter(form.errors.values()))[0] if form.errors else "Invalid booking parameters."
            return self._handle_error(request, err_msg, status_code=400)

        data = form.cleaned_data
        try:
            appointment = hold_appointment_slot(
                patient=request.user,
                doctor_id=data['doctor_id'],
                target_date=data['date'],
                start_time=data['time'],
                consultation_type=data.get('consultation_type') or Appointment.ConsultationType.PHYSICAL,
                patient_notes=data.get('patient_notes', '')
            )
        except SelfBookingError as err:
            return self._handle_error(request, str(err), status_code=400)
        except SlotUnavailableError as err:
            return self._handle_error(request, str(err), status_code=409)
        except DoctorUnavailableError as err:
            return self._handle_error(request, str(err), status_code=400)
        except BookingError as err:
            return self._handle_error(request, str(err), status_code=400)

        # Success: Return Checkout Modal Content
        confirm_form = AppointmentConfirmForm(initial={
            'consultation_type': appointment.consultation_type,
            'patient_notes': appointment.patient_notes
        })
        context = {
            'appointment': appointment,
            'doctor': appointment.doctor,
            'confirm_form': confirm_form,
            'now': timezone.now(),
        }

        if request.headers.get('HX-Request'):
            return render(request, 'appointments/partials/_checkout_modal_content.html', context)

        return redirect('patient_dashboard')

    def _handle_error(self, request, message: str, status_code: int = 400):
        if request.headers.get('HX-Request'):
            # Return an Out-of-Band (OOB) DaisyUI error toast so the user gets immediate feedback
            html = (
                f'<div id="toast-container" hx-swap-oob="beforeend">'
                f'  <div class="alert alert-error bg-rose-600 text-white shadow-xl rounded-2xl text-xs py-3 px-4 flex items-center justify-between">'
                f'    <span>{message}</span>'
                f'  </div>'
                f'</div>'
            )
            return HttpResponse(html, status=status_code)
        messages.error(request, message)
        return redirect(request.META.get('HTTP_REFERER', 'home'))


class AppointmentCancelHoldView(LoginRequiredMixin, View):
    """
    Cancels an active 10-minute hold and returns the slot to the public pool.
    """
    def post(self, request, appointment_id, *args, **kwargs):
        success = cancel_appointment_hold(user=request.user, appointment_id=appointment_id)
        if success:
            messages.info(request, "Appointment slot hold released successfully.")
        else:
            messages.warning(request, "Unable to release hold. The slot may have already expired.")

        if request.headers.get('HX-Request'):
            # Close modal and update toast
            return HttpResponse(
                '<div id="toast-container" hx-swap-oob="beforeend">'
                '  <div class="alert alert-info bg-sky-600 text-white shadow-xl rounded-2xl text-xs py-3 px-4">'
                '    Slot hold released.'
                '  </div>'
                '</div><script>document.getElementById("checkout-modal")?.close();</script>'
            )

        return redirect('patient_dashboard')


class PatientBookingsView(LoginRequiredMixin, View):
    """
    Lists the authenticated patient's current and past consultations.
    """
    def get(self, request, *args, **kwargs):
        appointments = Appointment.objects.select_related('doctor', 'doctor__user', 'doctor__department').filter(
            patient=request.user
        ).order_by('-appointment_date', '-start_time')

        context = {
            'appointments': appointments,
            'today': timezone.localdate(),
        }
        return render(request, 'appointments/my_bookings.html', context)


class AppointmentConfirmView(LoginRequiredMixin, View):
    """
    Confirms an active 10-minute hold reservation.
    Updates consultation mode, records symptoms/patient notes, transitions status to CONFIRMED.
    """
    def post(self, request, appointment_id, *args, **kwargs):
        form = AppointmentConfirmForm(request.POST)
        if not form.is_valid():
            err_msg = next(iter(form.errors.values()))[0] if form.errors else "Invalid confirmation parameters."
            messages.error(request, err_msg)
            return redirect(request.META.get('HTTP_REFERER', 'patient_bookings'))

        try:
            appointment = confirm_appointment_booking(
                user=request.user,
                appointment_id=appointment_id,
                consultation_type=form.cleaned_data.get('consultation_type'),
                patient_notes=form.cleaned_data.get('patient_notes', '')
            )
            messages.success(request, f"Appointment request submitted for {appointment.appointment_date.strftime('%B %d, %Y')} at {appointment.start_time.strftime('%I:%M %p')}. Waiting for doctor acceptance.")
        except (SlotUnavailableError, DoctorUnavailableError, BookingError) as err:
            messages.error(request, str(err))
            return redirect(request.META.get('HTTP_REFERER', 'doctor_directory'))

        redirect_url = reverse('appointment_detail', kwargs={'appointment_id': appointment.id})
        if request.headers.get('HX-Request'):
            response = HttpResponse(status=200)
            response['HX-Redirect'] = redirect_url
            return response

        return redirect(redirect_url)


class AppointmentDetailView(LoginRequiredMixin, View):
    """
    Displays the confirmed Appointment Receipt / Summary card.
    Accessible to the patient who booked and the assigned doctor.
    """
    def get(self, request, appointment_id, *args, **kwargs):
        appointment = get_object_or_404(
            Appointment.objects.select_related('doctor', 'doctor__user', 'doctor__department', 'patient'),
            Q(patient=request.user) | Q(doctor__user=request.user),
            id=appointment_id
        )

        context = {
            'appointment': appointment,
            'doctor': appointment.doctor,
            'is_patient': appointment.patient_id == request.user.id,
            'is_doctor': appointment.doctor.user_id == request.user.id,
            'is_telemed': appointment.consultation_type == Appointment.ConsultationType.TELEMEDICINE,
            'today': timezone.localdate(),
        }
        return render(request, 'appointments/confirmation_receipt.html', context)


class AppointmentCancelView(LoginRequiredMixin, View):
    """
    Cancels a confirmed appointment (by patient or doctor).
    """
    def post(self, request, appointment_id, *args, **kwargs):
        reason = request.POST.get('reason', '').strip()
        try:
            appointment = cancel_confirmed_appointment(
                user=request.user,
                appointment_id=appointment_id,
                cancellation_reason=reason
            )
            messages.info(request, f"Appointment on {appointment.appointment_date.strftime('%b %d')} has been cancelled.")
        except BookingError as err:
            messages.error(request, str(err))

        return redirect(request.META.get('HTTP_REFERER', 'patient_bookings'))


@method_decorator(doctor_required, name='dispatch')
class DoctorAppointmentAcceptView(LoginRequiredMixin, View):
    """
    Doctor accepts a pending consultation request.
    Transitions status: PENDING -> ACCEPTED.
    """
    def post(self, request, appointment_id, *args, **kwargs):
        try:
            appointment = accept_appointment(request.user, appointment_id)
            messages.success(
                request,
                f"Appointment with {appointment.patient.full_name} for {appointment.appointment_date.strftime('%b %d')} ({appointment.start_time.strftime('%I:%M %p')}) accepted."
            )
        except BookingError as err:
            messages.error(request, str(err))

        return redirect(request.META.get('HTTP_REFERER', 'doctor_dashboard'))


@method_decorator(doctor_required, name='dispatch')
class DoctorAppointmentRejectView(LoginRequiredMixin, View):
    """
    Doctor rejects a pending consultation request, returning the slot to the pool.
    Transitions status: PENDING -> REJECTED.
    """
    def post(self, request, appointment_id, *args, **kwargs):
        reason = request.POST.get('reason', '').strip()
        try:
            appointment = reject_appointment(request.user, appointment_id, reason=reason)
            messages.warning(
                request,
                f"Appointment request from {appointment.patient.full_name} has been rejected."
            )
        except BookingError as err:
            messages.error(request, str(err))

        return redirect(request.META.get('HTTP_REFERER', 'doctor_dashboard'))


@method_decorator(doctor_required, name='dispatch')
class DoctorAppointmentCompleteView(LoginRequiredMixin, View):
    """
    Doctor marks a finished consultation as completed.
    Transitions status: ACCEPTED / CONFIRMED -> COMPLETED.
    """
    def post(self, request, appointment_id, *args, **kwargs):
        try:
            appointment = complete_appointment(request.user, appointment_id)
            messages.success(
                request,
                f"Consultation with {appointment.patient.full_name} marked as completed."
            )
        except BookingError as err:
            messages.error(request, str(err))

        return redirect(request.META.get('HTTP_REFERER', 'doctor_dashboard'))



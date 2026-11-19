from datetime import date, time, datetime, timedelta
from typing import Optional
import uuid
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from apps.accounts.models import User
from apps.doctors.models import DoctorProfile, DoctorSchedule, DoctorLeave
from apps.appointments.models import Appointment
from apps.appointments.exceptions import (
    SlotUnavailableError,
    SelfBookingError,
    DoctorUnavailableError,
    BookingError,
)

def hold_appointment_slot(
    patient: User,
    doctor_id: uuid.UUID,
    target_date: date,
    start_time: time,
    consultation_type: str = Appointment.ConsultationType.PHYSICAL,
    patient_notes: str = ""
) -> Appointment:
    """
    Atomic Slot Reservation Engine.
    
    Places a 10-minute hold lock on a doctor's consultation slot.
    Guarantees concurrency safety using PostgreSQL row-level locks (select_for_update)
    within an atomic transaction, preventing double-bookings.
    """
    today = timezone.localdate()
    now_time = timezone.localtime().time()

    # 1. Past-date guard
    if target_date < today or (target_date == today and start_time <= now_time):
        raise SlotUnavailableError("Cannot reserve slots in the past.")

    # 2. Doctor Retrieval
    doctor = get_object_or_404(DoctorProfile, id=doctor_id, is_verified=True)

    # 3. Self-Booking Prevention (Option 1 Guardrail)
    if doctor.user_id == patient.id:
        raise SelfBookingError("You cannot book an appointment with yourself.")

    # 4. Doctor Leave Guard
    if DoctorLeave.objects.filter(doctor=doctor, leave_date=target_date).exists():
        raise DoctorUnavailableError("Doctor is on approved leave on this date.")

    # 5. Shift Schedule Verification & Slot Duration Lookup
    weekday = target_date.weekday()
    schedule = DoctorSchedule.objects.filter(
        doctor=doctor,
        day_of_week=weekday,
        is_active=True,
        start_time__lte=start_time,
        end_time__gt=start_time
    ).first()

    if not schedule:
        raise DoctorUnavailableError("Doctor has no active working shift covering this time.")

    # Calculate slot end time based on doctor's configured duration (e.g. 20 min)
    duration = timedelta(minutes=schedule.slot_duration_minutes)
    start_dt = datetime.combine(target_date, start_time)
    end_time = (start_dt + duration).time()

    # 6. ATOMIC TRANSACTION & PESSIMISTIC ROW LOCKING
    with transaction.atomic():
        # Check for active conflicting appointments (Confirmed, Accepted, Pending Review, OR Active 10-minute Hold)
        active_conflict = Appointment.objects.select_for_update().filter(
            doctor=doctor,
            appointment_date=target_date,
            start_time=start_time,
            status__in=[
                Appointment.Status.PENDING,
                Appointment.Status.ACCEPTED,
                Appointment.Status.CONFIRMED,
                Appointment.Status.PENDING_PAYMENT,
            ]
        ).filter(
            Q(status__in=[
                Appointment.Status.PENDING,
                Appointment.Status.ACCEPTED,
                Appointment.Status.CONFIRMED,
            ]) | Q(expires_at__gt=timezone.now())
        ).exists()

        if active_conflict:
            raise SlotUnavailableError("This slot was just claimed by another patient. Please choose another time.")

        # 7. Create Appointment with 10-Minute Hold Window
        expires_at = timezone.now() + timedelta(minutes=10)
        
        appointment = Appointment(
            patient=patient,
            doctor=doctor,
            appointment_date=target_date,
            start_time=start_time,
            end_time=end_time,
            consultation_type=consultation_type,
            status=Appointment.Status.PENDING_PAYMENT,
            expires_at=expires_at,
            patient_notes=patient_notes.strip() if patient_notes else ""
        )
        appointment.generate_telemed_room_id()
        appointment.full_clean()
        appointment.save()

        return appointment


def cancel_appointment_hold(user: User, appointment_id: uuid.UUID) -> bool:
    """
    Releases an active 10-minute slot hold, making the slot available again immediately.
    """
    with transaction.atomic():
        appointment = Appointment.objects.select_for_update().filter(
            id=appointment_id,
            patient=user,
            status=Appointment.Status.PENDING_PAYMENT
        ).first()

        if not appointment:
            return False

        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=['status'])
        return True


def confirm_appointment_booking(
    user: User,
    appointment_id: uuid.UUID,
    consultation_type: Optional[str] = None,
    patient_notes: str = ""
) -> Appointment:
    """
    Confirms an active 10-minute slot hold, transitioning it to PENDING status
    for the doctor's clinical review and acceptance.
    """
    with transaction.atomic():
        appointment = Appointment.objects.select_for_update().filter(
            id=appointment_id,
            patient=user
        ).first()

        if not appointment:
            raise BookingError("Appointment record not found or access denied.")

        if appointment.status in [Appointment.Status.PENDING, Appointment.Status.ACCEPTED, Appointment.Status.CONFIRMED]:
            return appointment

        if appointment.status != Appointment.Status.PENDING_PAYMENT:
            raise SlotUnavailableError(f"Cannot submit appointment with status {appointment.get_status_display()}.")

        if appointment.expires_at <= timezone.now():
            appointment.status = Appointment.Status.EXPIRED
            appointment.save(update_fields=['status'])
            raise SlotUnavailableError("Your 10-minute slot hold has expired. Please select another time.")

        # Update consultation mode if valid
        if consultation_type in Appointment.ConsultationType.values:
            if consultation_type == Appointment.ConsultationType.TELEMEDICINE and not appointment.doctor.is_available_for_telemed:
                raise DoctorUnavailableError("This doctor is currently not offering video teleconsultations.")
            appointment.consultation_type = consultation_type

        if patient_notes:
            appointment.patient_notes = patient_notes.strip()

        # Generate encrypted telemed room ID if video mode
        if appointment.consultation_type == Appointment.ConsultationType.TELEMEDICINE:
            appointment.generate_telemed_room_id()

        appointment.status = Appointment.Status.PENDING
        appointment.full_clean()
        appointment.save()

        return appointment


def accept_appointment(doctor_user: User, appointment_id: uuid.UUID) -> Appointment:
    """
    Doctor reviews and accepts a pending consultation request.
    Transitions status: PENDING -> ACCEPTED.
    """
    with transaction.atomic():
        appointment = Appointment.objects.select_for_update().filter(
            id=appointment_id,
            doctor__user=doctor_user
        ).first()

        if not appointment:
            raise BookingError("Appointment not found or you are not authorized to accept it.")

        if appointment.status != Appointment.Status.PENDING:
            raise BookingError(f"Cannot accept appointment with status {appointment.get_status_display()}.")

        appointment.status = Appointment.Status.ACCEPTED
        if appointment.consultation_type == Appointment.ConsultationType.TELEMEDICINE and not appointment.telemed_room_id:
            appointment.generate_telemed_room_id()

        appointment.save(update_fields=['status', 'telemed_room_id', 'updated_at'])
        return appointment


def reject_appointment(doctor_user: User, appointment_id: uuid.UUID, reason: str = "") -> Appointment:
    """
    Doctor rejects a pending consultation request, releasing the slot.
    Transitions status: PENDING -> REJECTED.
    """
    with transaction.atomic():
        appointment = Appointment.objects.select_for_update().filter(
            id=appointment_id,
            doctor__user=doctor_user
        ).first()

        if not appointment:
            raise BookingError("Appointment not found or you are not authorized to reject it.")

        if appointment.status != Appointment.Status.PENDING:
            raise BookingError(f"Cannot reject appointment with status {appointment.get_status_display()}.")

        appointment.status = Appointment.Status.REJECTED
        if reason:
            appointment.patient_notes = (appointment.patient_notes + f"\n[Rejected]: {reason}").strip()

        appointment.save(update_fields=['status', 'patient_notes', 'updated_at'])
        return appointment


def complete_appointment(doctor_user: User, appointment_id: uuid.UUID) -> Appointment:
    """
    Doctor marks a finished consultation as completed.
    Transitions status: ACCEPTED / CONFIRMED -> COMPLETED.
    """
    with transaction.atomic():
        appointment = Appointment.objects.select_for_update().filter(
            id=appointment_id,
            doctor__user=doctor_user
        ).first()

        if not appointment:
            raise BookingError("Appointment not found or you are not authorized to complete it.")

        if appointment.status not in [Appointment.Status.ACCEPTED, Appointment.Status.CONFIRMED]:
            raise BookingError(f"Cannot complete appointment with status {appointment.get_status_display()}.")

        appointment.status = Appointment.Status.COMPLETED
        appointment.save(update_fields=['status', 'updated_at'])
        return appointment


def cancel_confirmed_appointment(
    user: User,
    appointment_id: uuid.UUID,
    cancellation_reason: str = ""
) -> Appointment:
    """
    Cancels an appointment (callable by patient or doctor).
    """
    with transaction.atomic():
        appointment = Appointment.objects.select_for_update().filter(
            id=appointment_id
        ).filter(
            Q(patient=user) | Q(doctor__user=user)
        ).first()

        if not appointment:
            raise BookingError("Appointment not found or you are not authorized to cancel it.")

        if appointment.status in [
            Appointment.Status.CANCELLED,
            Appointment.Status.REJECTED,
            Appointment.Status.EXPIRED,
            Appointment.Status.COMPLETED,
        ]:
            raise BookingError(f"Cannot cancel appointment with status {appointment.get_status_display()}.")

        appointment.status = Appointment.Status.CANCELLED
        if cancellation_reason:
            appointment.patient_notes = (appointment.patient_notes + f"\n[Cancelled]: {cancellation_reason}").strip()
        appointment.save(update_fields=['status', 'patient_notes', 'updated_at'])
        return appointment


def release_expired_holds() -> int:
    """
    Sweeper routine to transition lapsed holds to EXPIRED status.
    Called periodically or before slot calculation queries.
    """
    now = timezone.now()
    count = Appointment.objects.filter(
        status=Appointment.Status.PENDING_PAYMENT,
        expires_at__lte=now
    ).update(status=Appointment.Status.EXPIRED)
    return count

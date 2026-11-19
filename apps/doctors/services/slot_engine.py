from datetime import date, datetime, timedelta, time
from typing import Dict, Any, List
from django.utils import timezone
from apps.doctors.models import DoctorProfile, DoctorSchedule, DoctorLeave

def compute_available_slots(doctor: DoctorProfile, target_date: date) -> Dict[str, Any]:
    """
    Pure Python Slot Availability Engine for Swasthya-Sewa.
    
    Dynamically generates time intervals for a doctor on a target date,
    verifying past-date rules, doctor leaves, weekly recurring shifts,
    and active appointment bookings.
    
    Returns structured slot telemetry with status: AVAILABLE, BOOKED, or EXPIRED.
    """
    today = timezone.localdate()
    now_time = timezone.localtime().time()

    base_response = {
        'doctor_id': str(doctor.id),
        'doctor_name': doctor.user.full_name,
        'department': doctor.department.name,
        'date': target_date.isoformat(),
        'day_name': target_date.strftime('%A'),
        'fee_physical': str(doctor.fee_physical),
        'fee_video': str(doctor.fee_video),
        'total_slots': 0,
        'available_slots_count': 0,
        'slots': [],
    }

    # 1. Past-date validation check
    if target_date < today:
        base_response.update({
            'status': 'PAST_DATE',
            'message': 'Cannot query or book appointment slots for past dates.',
        })
        return base_response

    # 2. Doctor Leave Check
    leave = DoctorLeave.objects.filter(doctor=doctor, leave_date=target_date).first()
    if leave:
        base_response.update({
            'status': 'DOCTOR_ON_LEAVE',
            'message': f"Doctor is on leave on {target_date.strftime('%b %d, %Y')}: {leave.reason or 'Personal Leave'}.",
        })
        return base_response

    # 3. Schedule Lookup for Target Day of the Week (0 = Monday ... 6 = Sunday)
    weekday = target_date.weekday()
    schedules = DoctorSchedule.objects.filter(
        doctor=doctor,
        day_of_week=weekday,
        is_active=True
    ).order_by('start_time')

    if not schedules.exists():
        base_response.update({
            'status': 'NOT_SCHEDULED',
            'message': f"Doctor has no scheduled working shifts on {target_date.strftime('%A')}s.",
        })
        return base_response

    # 4. Query Existing Bookings for this Doctor & Date (Appointments Phase 3 bridge)
    booked_times = set()
    try:
        from apps.appointments.models import Appointment
        from apps.appointments.services.booking_service import release_expired_holds
        from django.db.models import Q

        # Automatically sweep any lapsed 10-minute holds before evaluating slots
        release_expired_holds()

        active_bookings = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=target_date,
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
        ).values_list('start_time', flat=True)
        booked_times = {t.strftime('%H:%M') for t in active_bookings if t}
    except (ImportError, Exception):
        # Gracefully handle when appointments app/table is not yet migrated
        pass

    # 5. Generate Discrete Slots across each Active Shift
    generated_slots: List[Dict[str, Any]] = []

    for shift in schedules:
        duration = timedelta(minutes=shift.slot_duration_minutes)
        current_dt = datetime.combine(target_date, shift.start_time)
        shift_end_dt = datetime.combine(target_date, shift.end_time)

        while current_dt + duration <= shift_end_dt:
            slot_start_time = current_dt.time()
            slot_end_time = (current_dt + duration).time()
            time_str = slot_start_time.strftime('%H:%M')

            # Determine slot availability status
            if time_str in booked_times:
                slot_status = 'BOOKED'
                is_bookable = False
            elif target_date == today and slot_start_time <= now_time:
                slot_status = 'EXPIRED'
                is_bookable = False
            else:
                slot_status = 'AVAILABLE'
                is_bookable = True

            generated_slots.append({
                'time': time_str,
                'formatted_time': slot_start_time.strftime('%I:%M %p').lstrip('0'),
                'end_time': slot_end_time.strftime('%H:%M'),
                'formatted_end_time': slot_end_time.strftime('%I:%M %p').lstrip('0'),
                'duration_minutes': shift.slot_duration_minutes,
                'status': slot_status,
                'is_bookable': is_bookable,
            })

            current_dt += duration

    available_count = sum(1 for s in generated_slots if s['is_bookable'])

    base_response.update({
        'status': 'SUCCESS',
        'message': f"Found {available_count} available slot(s) for {target_date.strftime('%A, %b %d')}.",
        'total_slots': len(generated_slots),
        'available_slots_count': available_count,
        'slots': generated_slots,
    })

    return base_response

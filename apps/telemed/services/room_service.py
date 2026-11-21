import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any
from django.conf import settings
from django.utils import timezone
from apps.appointments.models import Appointment

class TelemedRoomService:
    """
    Security Guard and Orchestration Service for Telemedicine Video Rooms.
    Enforces participant authorization, time-window access gates, and room identification.
    """

    @classmethod
    def generate_room_name(cls, appointment_id: str, doctor_id: str) -> str:
        """
        Generates an unguessable cryptographic room name using HMAC-SHA256:
        swasthya-<hmac_sha256(appointment_id + doctor_id, SECRET_KEY)[:24]>
        """
        message = f"{appointment_id}-{doctor_id}".encode('utf-8')
        secret = settings.SECRET_KEY.encode('utf-8')
        signature = hmac.new(secret, message, hashlib.sha256).hexdigest()[:24]
        return f"swasthya-{signature}"

    @classmethod
    def verify_telemed_access(
        cls,
        user,
        appointment_id,
        time_buffer_minutes: int = 15
    ) -> Tuple[bool, str, Optional[Appointment], Optional[Dict[str, Any]]]:
        """
        Validates whether the user is permitted to enter the teleconsultation room.
        
        Security checks:
        1. Appointment exists and mode is TELEMEDICINE.
        2. User is either the booked patient or the assigned doctor.
        3. Appointment is in valid active state (ACCEPTED, CONFIRMED, or COMPLETED).
        4. Current time is within the allowed consultation window (-15 mins to +2 hours).

        Returns: (is_authorized: bool, error_message: str, appointment: Appointment, context: dict)
        """
        appointment = Appointment.objects.select_related(
            'doctor__user',
            'doctor__department',
            'patient'
        ).filter(id=appointment_id).first()

        if not appointment:
            return False, "Consultation record not found.", None, None

        # 1. Mode Check
        if appointment.consultation_type != Appointment.ConsultationType.TELEMEDICINE:
            return False, "This is an in-person hospital OPD visit, not a video teleconsultation.", appointment, None

        # 2. Identity Check (Only patient or assigned doctor)
        is_doctor = (user.id == appointment.doctor.user.id)
        is_patient = (user.id == appointment.patient.id)

        if not (is_doctor or is_patient):
            return False, "Access Denied: You are not authorized to join this private medical room.", appointment, None

        # 3. Status Gate Check
        if appointment.status == Appointment.Status.PENDING_PAYMENT:
            return False, "Consultation fee payment has not been completed.", appointment, None
        elif appointment.status == Appointment.Status.PENDING:
            return False, "This consultation is still pending doctor acceptance.", appointment, None
        elif appointment.status in [Appointment.Status.CANCELLED, Appointment.Status.REJECTED, Appointment.Status.EXPIRED]:
            return False, f"Cannot enter room: Consultation is {appointment.get_status_display().lower()}.", appointment, None

        # 4. Time Gate Check (Opens 15 minutes before slot; stays open for 3 hours on appointment date)
        now_local = timezone.localtime(timezone.now())
        appt_date = appointment.appointment_date
        slot_start_dt = timezone.make_aware(
            datetime.combine(appt_date, appointment.start_time),
            timezone.get_current_timezone()
        )
        early_window_start = slot_start_dt - timedelta(minutes=time_buffer_minutes)
        late_window_end = slot_start_dt + timedelta(hours=3)

        # Allow immediate access for today's appointment if within buffer window
        if now_local < early_window_start:
            mins_remaining = int((early_window_start - now_local).total_seconds() // 60)
            return (
                False,
                f"The consultation room will unlock {time_buffer_minutes} minutes before your appointment time (in ~{mins_remaining} minutes).",
                appointment,
                None
            )
        elif now_local > late_window_end and appointment.status == Appointment.Status.COMPLETED:
            # Already completed and past window
            return False, "This consultation session has ended.", appointment, None

        # Ensure telemed_room_id is initialized
        if not appointment.telemed_room_id:
            room_name = cls.generate_room_name(str(appointment.id), str(appointment.doctor.id))
            appointment.telemed_room_id = room_name
            appointment.save(update_fields=['telemed_room_id', 'updated_at'])
        else:
            room_name = appointment.telemed_room_id

        # Build participant context
        if is_doctor:
            doc_name = appointment.doctor.user.full_name.strip()
            display_name = doc_name if doc_name.lower().startswith('dr.') else f"Dr. {doc_name}"
            user_role = 'doctor'
        else:
            display_name = appointment.patient.full_name.strip()
            user_role = 'patient'

        context = {
            'room_name': room_name,
            'user_role': user_role,
            'is_doctor': is_doctor,
            'is_patient': is_patient,
            'display_name': display_name,
            'user_email': user.email,
            'doctor_name': appointment.doctor.user.full_name,
            'patient_name': appointment.patient.full_name,
            'department_name': appointment.doctor.department.name,
            'scheduled_time': f"{appointment.appointment_date.strftime('%A, %b %d')} at {appointment.start_time.strftime('%I:%M %p')}",
        }

        return True, "", appointment, context

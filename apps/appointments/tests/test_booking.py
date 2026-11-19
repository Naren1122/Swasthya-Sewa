from datetime import time, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import User
from apps.doctors.models import Department, DoctorProfile, DoctorSchedule
from apps.appointments.models import Appointment
from apps.appointments.services.booking_service import (
    hold_appointment_slot,
    cancel_appointment_hold,
    release_expired_holds,
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
)

class AppointmentBookingTests(TestCase):
    """
    Test suite verifying the atomic appointment reservation engine,
    self-booking prevention (Option 1), and cancellation.
    """
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name='Cardiology', icon_name='heart-pulse')

        # Doctor 1
        self.doc_user1 = User.objects.create_user(
            email='dr.aarav@hospital.com',
            password='Password123!',
            full_name='Dr. Aarav Sharma',
            role=User.Role.DOCTOR
        )
        self.doctor1 = DoctorProfile.objects.create(
            user=self.doc_user1,
            department=self.dept,
            nmc_number='11223',
            fee_physical=800,
            fee_video=1000,
            is_verified=True
        )

        # Doctor 2
        self.doc_user2 = User.objects.create_user(
            email='dr.binod@hospital.com',
            password='Password123!',
            full_name='Dr. Binod Karki',
            role=User.Role.DOCTOR
        )
        self.doctor2 = DoctorProfile.objects.create(
            user=self.doc_user2,
            department=self.dept,
            nmc_number='44556',
            fee_physical=900,
            fee_video=1100,
            is_verified=True
        )

        # Regular Patient
        self.patient = User.objects.create_user(
            email='patient.ramesh@gmail.com',
            password='Password123!',
            full_name='Ramesh Thapa',
            role=User.Role.PATIENT
        )

        # Setup working shift for Thursday for Doctor 1 (09:00 - 13:00, 20m slots)
        DoctorSchedule.objects.create(
            doctor=self.doctor1,
            day_of_week=3,  # Thursday
            start_time=time(9, 0),
            end_time=time(13, 0),
            slot_duration_minutes=20,
            is_active=True
        )

        # Target upcoming Thursday
        today = timezone.localdate()
        days_ahead = 3 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        self.target_thursday = today + timedelta(days=days_ahead)

    def test_patient_can_hold_available_slot(self):
        """Verify patient successfully places a 10-minute hold on a slot."""
        slot_time = time(9, 20)
        appointment = hold_appointment_slot(
            patient=self.patient,
            doctor_id=self.doctor1.id,
            target_date=self.target_thursday,
            start_time=slot_time,
            consultation_type=Appointment.ConsultationType.PHYSICAL
        )

        self.assertEqual(appointment.status, Appointment.Status.PENDING_PAYMENT)
        self.assertTrue(appointment.is_hold_active)
        self.assertEqual(appointment.end_time, time(9, 40))
        self.assertIsNotNone(appointment.telemed_room_id)

    def test_self_booking_is_strictly_forbidden(self):
        """Verify Option 1 guard: Doctor cannot book an appointment with themselves."""
        with self.assertRaises(SelfBookingError):
            hold_appointment_slot(
                patient=self.doc_user1,  # Same user as doctor1
                doctor_id=self.doctor1.id,
                target_date=self.target_thursday,
                start_time=time(9, 0)
            )

    def test_doctor_can_book_another_doctor_as_patient(self):
        """Verify Option 1: Doctor 2 can book Doctor 1 as a patient."""
        appointment = hold_appointment_slot(
            patient=self.doc_user2,  # Dr. Binod booking Dr. Aarav
            doctor_id=self.doctor1.id,
            target_date=self.target_thursday,
            start_time=time(10, 0),
            consultation_type=Appointment.ConsultationType.TELEMEDICINE
        )
        self.assertEqual(appointment.patient, self.doc_user2)
        self.assertEqual(appointment.doctor, self.doctor1)
        self.assertEqual(appointment.fee, 1000)

    def test_duplicate_hold_attempt_raises_slot_unavailable(self):
        """Verify atomic concurrency lock: Second patient attempting same slot is rejected."""
        slot_time = time(10, 20)
        # First patient claims slot
        hold_appointment_slot(
            patient=self.patient,
            doctor_id=self.doctor1.id,
            target_date=self.target_thursday,
            start_time=slot_time
        )

        # Second patient tries to claim the same slot
        with self.assertRaises(SlotUnavailableError):
            hold_appointment_slot(
                patient=self.doc_user2,
                doctor_id=self.doctor1.id,
                target_date=self.target_thursday,
                start_time=slot_time
            )

    def test_cancel_appointment_hold_releases_slot(self):
        """Verify releasing a hold frees up the slot immediately."""
        slot_time = time(11, 0)
        app = hold_appointment_slot(
            patient=self.patient,
            doctor_id=self.doctor1.id,
            target_date=self.target_thursday,
            start_time=slot_time
        )

        cancelled = cancel_appointment_hold(user=self.patient, appointment_id=app.id)
        self.assertTrue(cancelled)
        app.refresh_from_db()
        self.assertEqual(app.status, Appointment.Status.CANCELLED)

        # Now another patient can immediately claim it
        new_app = hold_appointment_slot(
            patient=self.doc_user2,
            doctor_id=self.doctor1.id,
            target_date=self.target_thursday,
            start_time=slot_time
        )
        self.assertEqual(new_app.status, Appointment.Status.PENDING_PAYMENT)

    def test_confirm_appointment_booking(self):
        """Verify patient can confirm an active hold and it transitions to PENDING."""
        app = hold_appointment_slot(
            patient=self.patient,
            doctor_id=self.doctor1.id,
            target_date=self.target_thursday,
            start_time=time(11, 20)
        )
        confirmed = confirm_appointment_booking(
            user=self.patient,
            appointment_id=app.id,
            consultation_type=Appointment.ConsultationType.TELEMEDICINE,
            patient_notes="Experiencing chest discomfort and mild dizziness."
        )
        self.assertEqual(confirmed.status, Appointment.Status.PENDING)
        self.assertEqual(confirmed.consultation_type, Appointment.ConsultationType.TELEMEDICINE)
        self.assertIn("chest discomfort", confirmed.patient_notes)
        self.assertIsNotNone(confirmed.telemed_room_id)

    def test_doctor_can_accept_and_complete_appointment(self):
        """Verify doctor can accept a pending request and mark it complete."""
        app = hold_appointment_slot(
            patient=self.patient,
            doctor_id=self.doctor1.id,
            target_date=self.target_thursday,
            start_time=time(9, 40)
        )
        confirm_appointment_booking(user=self.patient, appointment_id=app.id)

        # Doctor accepts
        accepted = accept_appointment(doctor_user=self.doc_user1, appointment_id=app.id)
        self.assertEqual(accepted.status, Appointment.Status.ACCEPTED)

        # Doctor marks completed
        completed = complete_appointment(doctor_user=self.doc_user1, appointment_id=app.id)
        self.assertEqual(completed.status, Appointment.Status.COMPLETED)

    def test_doctor_can_reject_pending_appointment(self):
        """Verify doctor can reject a pending request, freeing the slot."""
        app = hold_appointment_slot(
            patient=self.patient,
            doctor_id=self.doctor1.id,
            target_date=self.target_thursday,
            start_time=time(10, 40)
        )
        confirm_appointment_booking(user=self.patient, appointment_id=app.id)

        # Doctor rejects
        rejected = reject_appointment(
            doctor_user=self.doc_user1,
            appointment_id=app.id,
            reason="Unavailable due to emergency surgery."
        )
        self.assertEqual(rejected.status, Appointment.Status.REJECTED)
        self.assertIn("[Rejected]: Unavailable due to emergency surgery.", rejected.patient_notes)

    def test_cannot_confirm_expired_hold(self):
        """Verify confirmation is rejected if the 10-minute hold window has lapsed."""
        app = hold_appointment_slot(
            patient=self.patient,
            doctor_id=self.doctor1.id,
            target_date=self.target_thursday,
            start_time=time(11, 40)
        )
        # Artificially expire the hold
        Appointment.objects.filter(id=app.id).update(expires_at=timezone.now() - timedelta(minutes=1))

        with self.assertRaises(SlotUnavailableError):
            confirm_appointment_booking(
                user=self.patient,
                appointment_id=app.id
            )

    def test_cancel_confirmed_appointment(self):
        """Verify cancelling an already confirmed appointment."""
        app = hold_appointment_slot(
            patient=self.patient,
            doctor_id=self.doctor1.id,
            target_date=self.target_thursday,
            start_time=time(12, 0)
        )
        confirm_appointment_booking(user=self.patient, appointment_id=app.id)

        cancelled = cancel_confirmed_appointment(
            user=self.patient,
            appointment_id=app.id,
            cancellation_reason="Urgent travel required."
        )
        self.assertEqual(cancelled.status, Appointment.Status.CANCELLED)
        self.assertIn("[Cancelled]: Urgent travel required.", cancelled.patient_notes)

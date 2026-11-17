from datetime import date, time, timedelta
from django.test import TestCase
from django.utils import timezone
from apps.accounts.models import User
from apps.doctors.models import Department, DoctorProfile, DoctorSchedule, DoctorLeave
from apps.doctors.services.slot_engine import compute_available_slots

class SlotEngineTests(TestCase):
    """
    Unit test suite verifying the pure Python Slot Calculation Engine.
    """
    def setUp(self):
        self.dept = Department.objects.create(name='Pediatrics', icon_name='baby')
        self.doc_user = User.objects.create_user(
            email='dr.priya@hospital.com',
            password='StrongPassword123!',
            full_name='Dr. Priya Thapa',
            role=User.Role.DOCTOR
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doc_user,
            department=self.dept,
            nmc_number='98765',
            qualifications='MBBS, MD Pediatrics',
            is_verified=True
        )

        # Set shift for Monday: 09:00 AM - 10:00 AM (20-min slots -> 3 slots)
        self.monday_shift = DoctorSchedule.objects.create(
            doctor=self.doctor,
            day_of_week=0,  # Monday
            start_time=time(9, 0),
            end_time=time(10, 0),
            slot_duration_minutes=20,
            is_active=True
        )

    def _get_next_weekday(self, target_weekday: int) -> date:
        """Helper to find the next future occurrence of a given weekday (0=Mon...6=Sun)."""
        today = timezone.localdate()
        days_ahead = target_weekday - today.weekday()
        if days_ahead <= 0:  # Target day already happened this week, jump to next week
            days_ahead += 7
        return today + timedelta(days=days_ahead)

    def test_slot_engine_generates_exact_discrete_slots(self):
        """
        Verify that a 09:00-10:00 shift with 20-min duration generates
        exactly 3 slots: 09:00, 09:20, and 09:40.
        """
        future_monday = self._get_next_weekday(0)
        result = compute_available_slots(self.doctor, future_monday)

        self.assertEqual(result['status'], 'SUCCESS')
        self.assertEqual(result['total_slots'], 3)
        self.assertEqual(result['available_slots_count'], 3)

        times = [slot['time'] for slot in result['slots']]
        self.assertEqual(times, ['09:00', '09:20', '09:40'])

        # Verify formatting
        self.assertEqual(result['slots'][0]['formatted_time'], '9:00 AM')
        self.assertEqual(result['slots'][0]['end_time'], '09:20')
        self.assertTrue(result['slots'][0]['is_bookable'])

    def test_slot_engine_rejects_past_date(self):
        """Verify past date returns PAST_DATE status and zero slots."""
        past_date = timezone.localdate() - timedelta(days=1)
        result = compute_available_slots(self.doctor, past_date)

        self.assertEqual(result['status'], 'PAST_DATE')
        self.assertEqual(result['total_slots'], 0)
        self.assertIn('Cannot query or book', result['message'])

    def test_slot_engine_detects_doctor_leave(self):
        """Verify doctor on leave returns DOCTOR_ON_LEAVE status and zero slots."""
        future_monday = self._get_next_weekday(0)
        DoctorLeave.objects.create(
            doctor=self.doctor,
            leave_date=future_monday,
            reason='Medical Conference in Pokhara'
        )

        result = compute_available_slots(self.doctor, future_monday)
        self.assertEqual(result['status'], 'DOCTOR_ON_LEAVE')
        self.assertEqual(result['total_slots'], 0)
        self.assertIn('Medical Conference', result['message'])

    def test_slot_engine_returns_not_scheduled_for_unscheduled_day(self):
        """Verify day without active schedule returns NOT_SCHEDULED status."""
        # Find next Tuesday (1), which has no schedule
        future_tuesday = self._get_next_weekday(1)
        result = compute_available_slots(self.doctor, future_tuesday)

        self.assertEqual(result['status'], 'NOT_SCHEDULED')
        self.assertEqual(result['total_slots'], 0)
        self.assertIn('no scheduled working shifts', result['message'])

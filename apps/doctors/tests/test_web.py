from datetime import time, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import User
from apps.doctors.models import Department, DoctorProfile, DoctorSchedule

class DoctorWebTests(TestCase):
    """
    Test suite verifying Doctor Web UI views and HTMX partial endpoints.
    """
    def setUp(self):
        self.client = Client()

        self.dept = Department.objects.create(name='Orthopedics', icon_name='activity')
        self.user = User.objects.create_user(
            email='dr.karki@hospital.com',
            password='StrongPassword123!',
            full_name='Dr. Binod Karki',
            role=User.Role.DOCTOR
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.user,
            department=self.dept,
            nmc_number='44332',
            qualifications='MBBS, MS Ortho',
            is_verified=True,
            is_available_for_telemed=True
        )

        # Set shift for Thursday: 14:00 - 15:00 (20m -> 3 slots)
        self.shift = DoctorSchedule.objects.create(
            doctor=self.doctor,
            day_of_week=3,  # Thursday
            start_time=time(14, 0),
            end_time=time(15, 0),
            slot_duration_minutes=20,
            is_active=True
        )

    def test_doctor_directory_page_renders_successfully(self):
        """Verify GET /doctors/ renders doctor cards and department filters."""
        response = self.client.get(reverse('doctor_directory'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dr. Binod Karki')
        self.assertContains(response, 'Orthopedics')

    def test_doctor_directory_htmx_search_returns_partial(self):
        """Verify HTMX request to /doctors/?q=Binod returns partial template."""
        response = self.client.get(
            reverse('doctor_directory') + '?q=Binod',
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dr. Binod Karki')
        self.assertNotContains(response, '<!DOCTYPE html>')

    def test_doctor_detail_page_loads_via_seo_slug(self):
        """Verify GET /doctors/{slug}/ loads profile, schedule, and 7-day upcoming strip."""
        response = self.client.get(reverse('doctor_detail', kwargs={'slug': self.doctor.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dr. Binod Karki')
        self.assertContains(response, '44332')
        self.assertContains(response, 'Select Slot')
        self.assertContains(response, 'Upcoming Days')
        self.assertContains(response, 'Next 7 Days')
        self.assertEqual(len(response.context['upcoming_days']), 7)
        self.assertIsNotNone(response.context['target_date'])

    def test_doctor_slots_htmx_partial_endpoint(self):
        """Verify HTMX call to /doctors/{slug}/slots/?date=... swaps slot grid."""
        today = timezone.localdate()
        days_ahead = 3 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        target_thursday = today + timedelta(days=days_ahead)

        url = reverse('doctor_slots_partial', kwargs={'slug': self.doctor.slug})
        response = self.client.get(f"{url}?date={target_thursday.isoformat()}", HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '3 Available Slot(s)')
        self.assertContains(response, '2:00 PM')
        self.assertContains(response, '2:20 PM')
        self.assertContains(response, '2:40 PM')

    def test_doctor_can_add_and_delete_shift(self):
        """Verify doctor can self-serve add and remove working shifts."""
        self.client.force_login(self.user)

        # 1. Add shift on Monday: 09:00 - 12:00 (20 min)
        response = self.client.post(reverse('doctor_schedule_create'), {
            'day_of_week': 0,
            'start_time': '09:00',
            'end_time': '12:00',
            'slot_duration_minutes': 20,
        })
        self.assertRedirects(response, reverse('doctor_dashboard'))
        self.assertTrue(DoctorSchedule.objects.filter(doctor=self.doctor, day_of_week=0).exists())

        # 2. Delete the created shift
        mon_shift = DoctorSchedule.objects.get(doctor=self.doctor, day_of_week=0)
        del_response = self.client.post(reverse('doctor_schedule_delete', kwargs={'schedule_id': mon_shift.id}))
        self.assertRedirects(del_response, reverse('doctor_dashboard'))
        self.assertFalse(DoctorSchedule.objects.filter(id=mon_shift.id).exists())

    def test_doctor_cannot_delete_other_doctor_shift(self):
        """Verify strict isolation: Doctor A cannot delete Doctor B's shift."""
        other_user = User.objects.create_user(
            email='dr.other@hospital.com',
            password='StrongPassword123!',
            full_name='Dr. Other Doctor',
            role=User.Role.DOCTOR
        )
        other_doctor = DoctorProfile.objects.create(
            user=other_user,
            department=self.dept,
            nmc_number='99999',
            is_verified=True
        )
        other_shift = DoctorSchedule.objects.create(
            doctor=other_doctor,
            day_of_week=1,
            start_time=time(10, 0),
            end_time=time(12, 0),
            slot_duration_minutes=20,
            is_active=True
        )

        # Logged in as self.user, attempt to delete other_shift
        self.client.force_login(self.user)
        response = self.client.post(reverse('doctor_schedule_delete', kwargs={'schedule_id': other_shift.id}))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(DoctorSchedule.objects.filter(id=other_shift.id).exists())

    def test_doctor_delete_already_deleted_shift_is_idempotent_and_redirects(self):
        """Verify deleting an already removed shift redirects cleanly without crashing."""
        self.client.force_login(self.user)
        import uuid
        non_existent_id = uuid.uuid4()
        response = self.client.post(reverse('doctor_schedule_delete', kwargs={'schedule_id': non_existent_id}))
        self.assertRedirects(response, reverse('doctor_dashboard'))

    def test_doctor_can_declare_and_cancel_leave(self):
        """Verify doctor can self-serve log and cancel out-of-office leaves."""
        self.client.force_login(self.user)
        tomorrow = timezone.localdate() + timedelta(days=1)

        # 1. Declare Leave
        response = self.client.post(reverse('doctor_leave_create'), {
            'leave_date': tomorrow.isoformat(),
            'reason': 'Family Vacation',
        })
        self.assertRedirects(response, reverse('doctor_dashboard'))
        from apps.doctors.models import DoctorLeave
        self.assertTrue(DoctorLeave.objects.filter(doctor=self.doctor, leave_date=tomorrow).exists())

        # 2. Cancel Leave
        leave = DoctorLeave.objects.get(doctor=self.doctor, leave_date=tomorrow)
        del_response = self.client.post(reverse('doctor_leave_delete', kwargs={'leave_id': leave.id}))
        self.assertRedirects(del_response, reverse('doctor_dashboard'))
        self.assertFalse(DoctorLeave.objects.filter(id=leave.id).exists())

    def test_doctor_can_toggle_telemed_availability(self):
        """Verify doctor can self-serve toggle video teleconsultation acceptance."""
        self.client.force_login(self.user)
        self.assertTrue(self.doctor.is_available_for_telemed)

        response = self.client.post(reverse('doctor_telemed_toggle'))
        self.assertRedirects(response, reverse('doctor_dashboard'))
        self.doctor.refresh_from_db()
        self.assertFalse(self.doctor.is_available_for_telemed)

        # Toggle back
        self.client.post(reverse('doctor_telemed_toggle'))
        self.doctor.refresh_from_db()
        self.assertTrue(self.doctor.is_available_for_telemed)


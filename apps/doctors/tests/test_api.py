from datetime import time, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.doctors.models import Department, DoctorProfile, DoctorSchedule

class DoctorAPITests(TestCase):
    """
    Test suite verifying Doctor & Department REST API endpoints.
    """
    def setUp(self):
        self.api_client = APIClient()

        self.dept_cardio = Department.objects.create(name='Cardiology', icon_name='heart')
        self.dept_neuro = Department.objects.create(name='Neurology', icon_name='brain')

        self.user_cardio = User.objects.create_user(
            email='dr.anil@hospital.com',
            password='StrongPassword123!',
            full_name='Dr. Anil Shrestha',
            role=User.Role.DOCTOR
        )
        self.doc_cardio = DoctorProfile.objects.create(
            user=self.user_cardio,
            department=self.dept_cardio,
            nmc_number='55441',
            qualifications='MBBS, MD',
            is_verified=True,
            is_available_for_telemed=True
        )

        # Set shift for Wednesday: 10:00 - 11:00 (30m slots -> 2 slots)
        self.shift = DoctorSchedule.objects.create(
            doctor=self.doc_cardio,
            day_of_week=2,  # Wednesday
            start_time=time(10, 0),
            end_time=time(11, 0),
            slot_duration_minutes=30,
            is_active=True
        )

    def test_department_list_api(self):
        """Verify GET /api/v1/departments/ returns active departments."""
        response = self.api_client.get(reverse('api_department_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [d['name'] for d in response.data]
        self.assertIn('Cardiology', names)
        self.assertIn('Neurology', names)

    def test_doctor_list_api_with_department_filter(self):
        """Verify GET /api/v1/doctors/ filters correctly by department slug."""
        response = self.api_client.get(reverse('api_doctor_list'), {'department': 'cardiology'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['full_name'], 'Dr. Anil Shrestha')

        # Filter by empty department
        response_empty = self.api_client.get(reverse('api_doctor_list'), {'department': 'neurology'})
        self.assertEqual(len(response_empty.data), 0)

    def test_doctor_detail_api_by_slug(self):
        """Verify GET /api/v1/doctors/{slug}/ retrieves doctor profile."""
        url = reverse('api_doctor_detail', kwargs={'slug': self.doc_cardio.slug})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], 'Dr. Anil Shrestha')
        self.assertEqual(response.data['nmc_number'], '55441')
        self.assertEqual(len(response.data['schedules']), 1)

    def test_doctor_slots_api(self):
        """Verify GET /api/v1/doctors/{slug}/slots/?date=YYYY-MM-DD computes slots."""
        # Find next Wednesday
        today = timezone.localdate()
        days_ahead = 2 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        target_wednesday = today + timedelta(days=days_ahead)

        url = reverse('api_doctor_slots', kwargs={'slug': self.doc_cardio.slug})
        response = self.api_client.get(url, {'date': target_wednesday.isoformat()})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'SUCCESS')
        self.assertEqual(response.data['total_slots'], 2)  # 10:00 - 11:00 with 30m
        self.assertEqual(response.data['slots'][0]['time'], '10:00')
        self.assertEqual(response.data['slots'][1]['time'], '10:30')

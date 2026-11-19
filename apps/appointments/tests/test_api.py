from datetime import time, timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from apps.accounts.models import User
from apps.doctors.models import Department, DoctorProfile, DoctorSchedule
from apps.appointments.models import Appointment

class AppointmentAPITests(APITestCase):
    """
    Test suite verifying RESTful API v1 endpoints for Appointments:
    holding slots, confirming reservations, releasing holds, and listing consultations.
    """
    def setUp(self):
        self.dept = Department.objects.create(name='Cardiology', icon_name='heart-pulse')

        # Doctor 1
        self.doc_user = User.objects.create_user(
            email='dr.anand@hospital.com',
            password='StrongPassword123!',
            full_name='Dr. Anand Pokhrel',
            role=User.Role.DOCTOR
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doc_user,
            department=self.dept,
            nmc_number='12345',
            fee_physical=800,
            fee_video=1000,
            is_verified=True,
            is_available_for_telemed=True
        )

        # Shift: Thursday 09:00 - 12:00 (20m slots)
        DoctorSchedule.objects.create(
            doctor=self.doctor,
            day_of_week=3,  # Thursday
            start_time=time(9, 0),
            end_time=time(12, 0),
            slot_duration_minutes=20,
            is_active=True
        )

        # Patient 1
        self.patient = User.objects.create_user(
            email='sita.shrestha@gmail.com',
            password='StrongPassword123!',
            full_name='Sita Shrestha',
            role=User.Role.PATIENT
        )

        # Doctor 2 (can book as patient)
        self.doc_user2 = User.objects.create_user(
            email='dr.bina@hospital.com',
            password='StrongPassword123!',
            full_name='Dr. Bina Rayamajhi',
            role=User.Role.DOCTOR
        )

        # Compute next upcoming Thursday
        today = timezone.localdate()
        days_ahead = 3 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        self.target_thursday = today + timedelta(days=days_ahead)

    def test_unauthenticated_hold_request_rejected(self):
        """Verify unauthenticated user cannot hold a slot (401/403)."""
        url = reverse('api_appointment_hold')
        response = self.client.post(url, {
            'doctor_id': str(self.doctor.id),
            'date': self.target_thursday.isoformat(),
            'time': '09:00:00'
        })
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_patient_can_hold_slot_via_api(self):
        """Verify authenticated patient can place 10-minute hold via REST API."""
        self.client.force_authenticate(user=self.patient)
        url = reverse('api_appointment_hold')
        payload = {
            'doctor_id': str(self.doctor.id),
            'date': self.target_thursday.isoformat(),
            'time': '09:00:00',
            'consultation_type': 'PHYSICAL',
            'patient_notes': 'Experiencing persistent chest tightness.'
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'PENDING_PAYMENT')
        self.assertTrue(response.data['is_hold_active'])
        self.assertEqual(response.data['patient_name'], 'Sita Shrestha')
        self.assertEqual(response.data['doctor_name'], 'Dr. Anand Pokhrel')

    def test_self_booking_guard_via_api(self):
        """Verify Doctor cannot book own slot via API (Option 1 Guard -> 400 Bad Request)."""
        self.client.force_authenticate(user=self.doc_user)
        url = reverse('api_appointment_hold')
        payload = {
            'doctor_id': str(self.doctor.id),
            'date': self.target_thursday.isoformat(),
            'time': '09:20:00',
            'consultation_type': 'PHYSICAL'
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cannot book an appointment with yourself", response.data['detail'])

    def test_doctor_can_book_another_doctor_via_api(self):
        """Verify Option 1: Doctor 2 can book Doctor 1 as a patient."""
        self.client.force_authenticate(user=self.doc_user2)
        url = reverse('api_appointment_hold')
        payload = {
            'doctor_id': str(self.doctor.id),
            'date': self.target_thursday.isoformat(),
            'time': '09:40:00',
            'consultation_type': 'TELEMEDICINE'
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'PENDING_PAYMENT')

    def test_duplicate_hold_returns_409_conflict(self):
        """Verify concurrent slot claim returns 409 Conflict."""
        self.client.force_authenticate(user=self.patient)
        url = reverse('api_appointment_hold')
        payload = {
            'doctor_id': str(self.doctor.id),
            'date': self.target_thursday.isoformat(),
            'time': '10:00:00'
        }
        res1 = self.client.post(url, payload, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Another patient attempts the same slot
        self.client.force_authenticate(user=self.doc_user2)
        res2 = self.client.post(url, payload, format='json')
        self.assertEqual(res2.status_code, status.HTTP_409_CONFLICT)

    def test_patient_can_confirm_hold_via_api(self):
        """Verify confirming hold transitions status to CONFIRMED."""
        self.client.force_authenticate(user=self.patient)
        hold_url = reverse('api_appointment_hold')
        hold_res = self.client.post(hold_url, {
            'doctor_id': str(self.doctor.id),
            'date': self.target_thursday.isoformat(),
            'time': '10:20:00'
        }, format='json')
        appointment_id = hold_res.data['id']

        confirm_url = reverse('api_appointment_confirm', kwargs={'appointment_id': appointment_id})
        confirm_res = self.client.post(confirm_url, {
            'consultation_type': 'TELEMEDICINE',
            'patient_notes': 'Need video consultation.'
        }, format='json')
        self.assertEqual(confirm_res.status_code, status.HTTP_200_OK)
        self.assertEqual(confirm_res.data['status'], 'PENDING')
        self.assertEqual(confirm_res.data['consultation_type'], 'TELEMEDICINE')
        self.assertIsNotNone(confirm_res.data['telemed_room_id'])

    def test_patient_can_release_hold_via_api(self):
        """Verify releasing hold frees the slot."""
        self.client.force_authenticate(user=self.patient)
        hold_url = reverse('api_appointment_hold')
        hold_res = self.client.post(hold_url, {
            'doctor_id': str(self.doctor.id),
            'date': self.target_thursday.isoformat(),
            'time': '10:40:00'
        }, format='json')
        appointment_id = hold_res.data['id']

        cancel_hold_url = reverse('api_appointment_cancel_hold', kwargs={'appointment_id': appointment_id})
        cancel_res = self.client.post(cancel_hold_url)
        self.assertEqual(cancel_res.status_code, status.HTTP_200_OK)

        # Slot can now be claimed again
        rehold_res = self.client.post(hold_url, {
            'doctor_id': str(self.doctor.id),
            'date': self.target_thursday.isoformat(),
            'time': '10:40:00'
        }, format='json')
        self.assertEqual(rehold_res.status_code, status.HTTP_201_CREATED)

    def test_patient_can_list_and_retrieve_appointments_via_api(self):
        """Verify patient list and retrieve endpoints."""
        self.client.force_authenticate(user=self.patient)
        hold_url = reverse('api_appointment_hold')
        hold_res = self.client.post(hold_url, {
            'doctor_id': str(self.doctor.id),
            'date': self.target_thursday.isoformat(),
            'time': '11:00:00'
        }, format='json')
        appointment_id = hold_res.data['id']

        # List
        list_url = reverse('api_patient_bookings')
        list_res = self.client.get(list_url)
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.data), 1)

        # Retrieve
        detail_url = reverse('api_appointment_detail', kwargs={'appointment_id': appointment_id})
        detail_res = self.client.get(detail_url)
        self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_res.data['id'], appointment_id)

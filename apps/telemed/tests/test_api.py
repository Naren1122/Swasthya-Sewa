from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.doctors.models import Department, DoctorProfile
from apps.appointments.models import Appointment
from apps.telemed.models import MedicalDocument, ConsultationNote

class TelemedAPITests(APITestCase):
    """
    Test suite for Telemedicine REST API v1:
    - GET /api/v1/telemed/appointments/{id}/room-access/
    - GET, POST /api/v1/telemed/appointments/{id}/documents/
    - GET, POST /api/v1/telemed/appointments/{id}/notes/
    """
    def setUp(self):
        self.dept = Department.objects.create(name='Neurology', icon_name='brain')

        self.doc_user = User.objects.create_user(
            email='dr.suresh@hospital.com',
            password='StrongPassword123!',
            full_name='Dr. Suresh Adhikari',
            role=User.Role.DOCTOR
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doc_user,
            department=self.dept,
            nmc_number='44556',
            fee_physical=700,
            fee_video=900,
            is_verified=True,
            is_available_for_telemed=True
        )

        self.patient = User.objects.create_user(
            email='patient.anup@gmail.com',
            password='StrongPassword123!',
            full_name='Anup Pandey',
            role=User.Role.PATIENT
        )

        today = timezone.localdate()
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=today,
            start_time=timezone.localtime(timezone.now()).time(),
            end_time=(timezone.localtime(timezone.now()) + timedelta(minutes=20)).time(),
            consultation_type=Appointment.ConsultationType.TELEMEDICINE,
            status=Appointment.Status.ACCEPTED,
            expires_at=timezone.now() + timedelta(days=1)
        )

        # Authenticate patient by default
        refresh = RefreshToken.for_user(self.patient)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_api_room_access_authorized(self):
        """Verify patient can retrieve telemed room credentials via API."""
        url = reverse('api_telemed_room_access', kwargs={'appointment_id': self.appointment.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['room_name'].startswith('swasthya-'))
        self.assertEqual(response.data['user_role'], 'patient')
        self.assertEqual(response.data['display_name'], 'Anup Pandey')

    def test_api_room_access_unauthorized_forbidden(self):
        """Verify unrelated user is denied telemed room access with 403."""
        stranger = User.objects.create_user(
            email='stranger.api@gmail.com',
            password='StrongPassword123!',
            full_name='Stranger API'
        )
        refresh = RefreshToken.for_user(stranger)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        url = reverse('api_telemed_room_access', kwargs={'appointment_id': self.appointment.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_document_upload_and_list(self):
        """Verify uploading and listing medical diagnostic documents via API."""
        url = reverse('api_telemed_documents', kwargs={'appointment_id': self.appointment.id})
        test_file = SimpleUploadedFile("mri_brain.pdf", b"%PDF-1.4 brain scan report", content_type="application/pdf")

        # Upload
        response = self.client.post(url, {
            'title': 'Brain MRI Scan',
            'document_type': MedicalDocument.DocumentType.IMAGING,
            'file': test_file,
            'notes': 'Normal scan report'
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Brain MRI Scan')

        # List
        list_res = self.client.get(url)
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.data), 1)

    def test_api_doctor_can_record_notes(self):
        """Verify doctor can write and retrieve consultation notes via API."""
        # Switch to doctor credentials
        refresh = RefreshToken.for_user(self.doc_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        url = reverse('api_telemed_notes', kwargs={'appointment_id': self.appointment.id})
        post_res = self.client.post(url, {
            'diagnosis': 'Tension Headache',
            'prescription': 'Naproxen 250mg SOS',
            'advice': 'Reduce screen time and stay hydrated',
            'finalize': 'false'
        }, format='multipart')

        self.assertEqual(post_res.status_code, status.HTTP_200_OK)
        self.assertEqual(post_res.data['diagnosis'], 'Tension Headache')

        # Retrieve
        get_res = self.client.get(url)
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(get_res.data['diagnosis'], 'Tension Headache')

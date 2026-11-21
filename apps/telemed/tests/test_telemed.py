import io
from datetime import time, timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.doctors.models import Department, DoctorProfile, DoctorSchedule
from apps.appointments.models import Appointment
from apps.telemed.models import MedicalDocument, ConsultationNote
from apps.telemed.services.room_service import TelemedRoomService

class TelemedicineBackendTests(TestCase):
    """
    Test suite verifying cryptographic room security, access control,
    document uploads, and doctor consultation notes.
    """
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name='Cardiology', icon_name='heart')

        self.doc_user = User.objects.create_user(
            email='dr.kiran@hospital.com',
            password='StrongPassword123!',
            full_name='Dr. Kiran Shrestha',
            role=User.Role.DOCTOR
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doc_user,
            department=self.dept,
            nmc_number='99221',
            fee_physical=600,
            fee_video=800,
            is_verified=True,
            is_available_for_telemed=True
        )

        self.patient = User.objects.create_user(
            email='patient.maya@gmail.com',
            password='StrongPassword123!',
            full_name='Maya Thapa',
            role=User.Role.PATIENT
        )

        self.third_party = User.objects.create_user(
            email='stranger@gmail.com',
            password='StrongPassword123!',
            full_name='Stranger User',
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

    def test_room_name_cryptographic_generation(self):
        """Verify room name generation follows unguessable HMAC format."""
        room1 = TelemedRoomService.generate_room_name("appt-123", "doc-456")
        room2 = TelemedRoomService.generate_room_name("appt-123", "doc-456")

        self.assertTrue(room1.startswith("swasthya-"))
        self.assertEqual(len(room1), len("swasthya-") + 24)
        self.assertEqual(room1, room2)

    def test_verify_telemed_access_patient_and_doctor(self):
        """Verify authorized patient and assigned doctor can access the video room."""
        # Patient
        ok, msg, appt, ctx = TelemedRoomService.verify_telemed_access(self.patient, self.appointment.id)
        self.assertTrue(ok)
        self.assertEqual(ctx['user_role'], 'patient')
        self.assertEqual(ctx['display_name'], 'Maya Thapa')
        self.assertTrue(ctx['room_name'].startswith('swasthya-'))

        # Doctor
        ok, msg, appt, ctx = TelemedRoomService.verify_telemed_access(self.doc_user, self.appointment.id)
        self.assertTrue(ok)
        self.assertEqual(ctx['user_role'], 'doctor')
        self.assertEqual(ctx['display_name'], 'Dr. Kiran Shrestha')

    def test_unauthorized_third_party_denied(self):
        """Verify unrelated user is blocked with access denied."""
        ok, msg, appt, ctx = TelemedRoomService.verify_telemed_access(self.third_party, self.appointment.id)
        self.assertFalse(ok)
        self.assertIn("Access Denied", msg)

    def test_physical_appointment_rejected(self):
        """Verify in-person hospital visit cannot open a telemed room."""
        self.appointment.consultation_type = Appointment.ConsultationType.PHYSICAL
        self.appointment.save()

        ok, msg, appt, ctx = TelemedRoomService.verify_telemed_access(self.patient, self.appointment.id)
        self.assertFalse(ok)
        self.assertIn("in-person", msg)

    def test_unconfirmed_appointment_status_gated(self):
        """Verify appointment still in PENDING (unaccepted) is gated."""
        self.appointment.status = Appointment.Status.PENDING
        self.appointment.save()

        ok, msg, appt, ctx = TelemedRoomService.verify_telemed_access(self.patient, self.appointment.id)
        self.assertFalse(ok)
        self.assertIn("pending", msg)

    def test_document_upload_web_view(self):
        """Verify patient can upload a medical diagnostic report."""
        self.client.force_login(self.patient)
        fake_file = SimpleUploadedFile("cbc_report.pdf", b"%PDF-1.4 test report content", content_type="application/pdf")

        url = reverse('telemed_document_upload', kwargs={'appointment_id': self.appointment.id})
        response = self.client.post(url, {
            'title': 'Blood Test CBC',
            'document_type': MedicalDocument.DocumentType.LAB_REPORT,
            'notes': 'Slightly high WBC count',
            'file': fake_file
        })

        self.assertEqual(response.status_code, 302)
        self.assertIn(str(self.appointment.id), response.url)
        self.assertTrue(MedicalDocument.objects.filter(appointment=self.appointment, title='Blood Test CBC').exists())

    def test_doctor_can_record_notes_and_finalize(self):
        """Verify doctor can record clinical notes and finalize to COMPLETED status."""
        self.client.force_login(self.doc_user)
        url = reverse('telemed_note_save', kwargs={'appointment_id': self.appointment.id})

        response = self.client.post(url, {
            'diagnosis': 'Acute Pharyngitis',
            'symptoms': 'Sore throat and mild fever for 2 days',
            'prescription': 'Paracetamol 500mg TDS, Azithromycin 500mg OD for 3 days',
            'advice': 'Warm saline gargle, rest, drink fluids',
            'finalize': 'true'
        })

        self.assertEqual(response.status_code, 302)
        self.assertIn(str(self.appointment.id), response.url)
        
        note = ConsultationNote.objects.get(appointment=self.appointment)
        self.assertEqual(note.diagnosis, 'Acute Pharyngitis')
        self.assertTrue(note.is_finalized)
        
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, Appointment.Status.COMPLETED)

    def test_patient_cannot_record_doctor_notes(self):
        """Verify patient cannot author doctor's clinical consultation notes."""
        self.client.force_login(self.patient)
        url = reverse('telemed_note_save', kwargs={'appointment_id': self.appointment.id})

        response = self.client.post(url, {
            'diagnosis': 'Self Diagnosis',
            'prescription': 'Self medication'
        })

        self.assertEqual(response.status_code, 403)

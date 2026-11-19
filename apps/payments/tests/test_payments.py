import base64
import json
from datetime import time, timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import User
from apps.doctors.models import Department, DoctorProfile, DoctorSchedule
from apps.appointments.models import Appointment
from apps.appointments.services.booking_service import hold_appointment_slot
from apps.payments.models import Payment
from apps.payments.services.esewa_service import EsewaPaymentService

class PaymentGatewayTests(TestCase):
    """
    Test suite verifying eSewa and Khalti payment services,
    HMAC-SHA256 signatures, cash on arrival, and callback verification.
    """
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name='Pediatrics', icon_name='baby')

        self.doc_user = User.objects.create_user(
            email='dr.anita@hospital.com',
            password='StrongPassword123!',
            full_name='Dr. Anita Gurung',
            role=User.Role.DOCTOR
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doc_user,
            department=self.dept,
            nmc_number='88990',
            fee_physical=700,
            fee_video=900,
            is_verified=True,
            is_available_for_telemed=True
        )

        DoctorSchedule.objects.create(
            doctor=self.doctor,
            day_of_week=3,  # Thursday
            start_time=time(10, 0),
            end_time=time(13, 0),
            slot_duration_minutes=20,
            is_active=True
        )

        self.patient = User.objects.create_user(
            email='patient.sunita@gmail.com',
            password='StrongPassword123!',
            full_name='Sunita KC',
            role=User.Role.PATIENT
        )

        today = timezone.localdate()
        days_ahead = 3 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        self.target_thursday = today + timedelta(days=days_ahead)

        # Create active 10-minute hold
        self.appointment = hold_appointment_slot(
            patient=self.patient,
            doctor_id=self.doctor.id,
            target_date=self.target_thursday,
            start_time=time(10, 0),
            consultation_type=Appointment.ConsultationType.PHYSICAL
        )

    def test_esewa_signature_generation(self):
        """Verify HMAC-SHA256 signature generation matches expected Base64 format."""
        message = "total_amount=700,transaction_uuid=test-uuid-1234,product_code=EPAYTEST"
        sig1 = EsewaPaymentService.generate_signature(message)
        sig2 = EsewaPaymentService.generate_signature(message)

        self.assertTrue(isinstance(sig1, str))
        self.assertGreater(len(sig1), 10)
        self.assertEqual(sig1, sig2)

    def test_cash_on_arrival_payment_initiation(self):
        """Verify selecting Cash on Arrival marks payment initiated and appointment PENDING."""
        self.client.force_login(self.patient)
        url = reverse('payment_initiate', kwargs={'appointment_id': self.appointment.id})
        response = self.client.post(url, {
            'gateway': 'CASH_ON_ARRIVAL',
            'consultation_type': 'PHYSICAL',
            'patient_notes': 'Paying at OPD counter'
        })

        self.assertRedirects(response, reverse('appointment_detail', kwargs={'appointment_id': self.appointment.id}))
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, Appointment.Status.PENDING)
        self.assertTrue(Payment.objects.filter(appointment=self.appointment, gateway=Payment.Gateway.CASH_ON_ARRIVAL).exists())

    def test_esewa_payment_initiation_renders_redirect_form(self):
        """Verify eSewa selection renders auto-submitting form with signed parameters."""
        self.client.force_login(self.patient)
        url = reverse('payment_initiate', kwargs={'appointment_id': self.appointment.id})
        response = self.client.post(url, {
            'gateway': 'ESEWA',
            'consultation_type': 'PHYSICAL'
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'esewa-form')
        self.assertContains(response, 'EPAYTEST')
        self.assertContains(response, 'signature')
        self.assertTrue(Payment.objects.filter(appointment=self.appointment, gateway=Payment.Gateway.ESEWA).exists())

    def test_esewa_success_callback_verifies_signature_and_confirms(self):
        """Verify valid eSewa callback marks payment SUCCESS and appointment PENDING."""
        self.client.force_login(self.patient)
        payment = Payment.objects.create(
            appointment=self.appointment,
            patient=self.patient,
            gateway=Payment.Gateway.ESEWA,
            amount=700,
            status=Payment.Status.INITIATED
        )

        # Construct valid mock eSewa v2 callback payload
        transaction_code = "000TEST999"
        status_val = "COMPLETE"
        total_amount = "700"
        transaction_uuid = str(payment.transaction_uuid)
        product_code = "EPAYTEST"
        signed_field_names = "transaction_code,status,total_amount,transaction_uuid,product_code,signed_field_names"

        sig_msg = f"transaction_code={transaction_code},status={status_val},total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code},signed_field_names={signed_field_names}"
        signature = EsewaPaymentService.generate_signature(sig_msg)

        payload_dict = {
            'transaction_code': transaction_code,
            'status': status_val,
            'total_amount': total_amount,
            'transaction_uuid': transaction_uuid,
            'product_code': product_code,
            'signed_field_names': signed_field_names,
            'signature': signature
        }
        encoded_data = base64.b64encode(json.dumps(payload_dict).encode('utf-8')).decode('utf-8')

        url = f"{reverse('esewa_success')}?data={encoded_data}"
        response = self.client.get(url)

        self.assertRedirects(response, reverse('appointment_detail', kwargs={'appointment_id': self.appointment.id}))
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.SUCCESS)
        self.assertEqual(payment.gateway_ref, transaction_code)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, Appointment.Status.PENDING)

    def test_esewa_tampered_signature_rejected(self):
        """Verify callback with tampered amount is caught and rejected."""
        self.client.force_login(self.patient)
        payment = Payment.objects.create(
            appointment=self.appointment,
            patient=self.patient,
            gateway=Payment.Gateway.ESEWA,
            amount=700,
            status=Payment.Status.INITIATED
        )

        # Invalid/fake signature
        payload_dict = {
            'transaction_code': 'FAKE123',
            'status': 'COMPLETE',
            'total_amount': '700',
            'transaction_uuid': str(payment.transaction_uuid),
            'product_code': 'EPAYTEST',
            'signed_field_names': 'transaction_code,status,total_amount,transaction_uuid,product_code,signed_field_names',
            'signature': 'INVALID_SIGNATURE_HERE'
        }
        encoded_data = base64.b64encode(json.dumps(payload_dict).encode('utf-8')).decode('utf-8')

        url = f"{reverse('esewa_success')}?data={encoded_data}"
        response = self.client.get(url)

        self.assertRedirects(response, reverse('patient_bookings'))
        payment.refresh_from_db()
        self.assertNotEqual(payment.status, Payment.Status.SUCCESS)

    @patch('requests.post')
    def test_khalti_payment_initiation(self, mock_post):
        """Verify Khalti payment initiation calls Khalti API and redirects to payment_url."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'pidx': 'test_pidx_abc123',
            'payment_url': 'https://test-pay.khalti.com/?pidx=test_pidx_abc123'
        }
        mock_post.return_value = mock_response

        self.client.force_login(self.patient)
        url = reverse('payment_initiate', kwargs={'appointment_id': self.appointment.id})
        response = self.client.post(url, {
            'gateway': 'KHALTI',
            'consultation_type': 'PHYSICAL'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'https://test-pay.khalti.com/?pidx=test_pidx_abc123')
        self.assertTrue(Payment.objects.filter(appointment=self.appointment, gateway=Payment.Gateway.KHALTI).exists())

    @patch('requests.post')
    def test_khalti_success_callback_verifies_and_confirms(self, mock_post):
        """Verify successful Khalti lookup marks payment SUCCESS and confirms appointment to PENDING."""
        self.client.force_login(self.patient)
        payment = Payment.objects.create(
            appointment=self.appointment,
            patient=self.patient,
            gateway=Payment.Gateway.KHALTI,
            gateway_ref='test_pidx_abc123',
            amount=700,
            status=Payment.Status.INITIATED
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'pidx': 'test_pidx_abc123',
            'total_amount': 70000,
            'status': 'Completed',
            'transaction_id': 'KHALTI_TXN_999'
        }
        mock_post.return_value = mock_response

        url = f"{reverse('khalti_callback')}?pidx=test_pidx_abc123"
        response = self.client.get(url)

        self.assertRedirects(response, reverse('appointment_detail', kwargs={'appointment_id': self.appointment.id}))
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.SUCCESS)
        self.assertEqual(payment.gateway_ref, 'test_pidx_abc123')
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, Appointment.Status.PENDING)


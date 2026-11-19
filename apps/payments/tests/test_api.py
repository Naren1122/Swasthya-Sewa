import base64
import json
from datetime import time, timedelta
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.doctors.models import Department, DoctorProfile, DoctorSchedule
from apps.appointments.models import Appointment
from apps.appointments.services.booking_service import hold_appointment_slot
from apps.payments.models import Payment
from apps.payments.services.esewa_service import EsewaPaymentService

class PaymentAPITests(APITestCase):
    """
    Test suite for Payments REST API v1 endpoints:
    - POST /api/v1/payments/initiate/
    - POST /api/v1/payments/verify/
    - GET  /api/v1/payments/
    - GET  /api/v1/payments/<uuid:id>/
    """
    def setUp(self):
        self.dept = Department.objects.create(name='Orthopedics', icon_name='bone')

        self.doc_user = User.objects.create_user(
            email='dr.rajesh@hospital.com',
            password='StrongPassword123!',
            full_name='Dr. Rajesh Sharma',
            role=User.Role.DOCTOR
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doc_user,
            department=self.dept,
            nmc_number='77889',
            fee_physical=800,
            fee_video=1000,
            is_verified=True,
            is_available_for_telemed=True
        )

        DoctorSchedule.objects.create(
            doctor=self.doctor,
            day_of_week=4,  # Friday
            start_time=time(9, 0),
            end_time=time(12, 0),
            slot_duration_minutes=20,
            is_active=True
        )

        self.patient = User.objects.create_user(
            email='patient.ramesh@gmail.com',
            password='StrongPassword123!',
            full_name='Ramesh Karki',
            role=User.Role.PATIENT
        )

        # Authenticate via JWT
        refresh = RefreshToken.for_user(self.patient)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        today = timezone.localdate()
        days_ahead = 4 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        self.target_friday = today + timedelta(days=days_ahead)

        # Create active 10-minute hold
        self.appointment = hold_appointment_slot(
            patient=self.patient,
            doctor_id=self.doctor.id,
            target_date=self.target_friday,
            start_time=time(9, 0),
            consultation_type=Appointment.ConsultationType.PHYSICAL
        )

    def test_api_initiate_cash_on_arrival(self):
        """Verify API initiation for Cash on Arrival confirms appointment to PENDING."""
        url = reverse('api_payment_initiate')
        response = self.client.post(url, {
            'appointment_id': str(self.appointment.id),
            'gateway': 'CASH_ON_ARRIVAL'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['gateway'], 'CASH_ON_ARRIVAL')
        self.assertEqual(response.data['status'], 'CONFIRMED')

        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, Appointment.Status.PENDING)
        self.assertTrue(Payment.objects.filter(appointment=self.appointment, gateway='CASH_ON_ARRIVAL').exists())

    def test_api_initiate_esewa(self):
        """Verify API initiation for eSewa returns cryptographic fields & action URL."""
        url = reverse('api_payment_initiate')
        response = self.client.post(url, {
            'appointment_id': str(self.appointment.id),
            'gateway': 'ESEWA'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['gateway'], 'ESEWA')
        self.assertIn('action_url', response.data)
        self.assertIn('fields', response.data)
        self.assertIn('signature', response.data['fields'])
        self.assertEqual(response.data['fields']['product_code'], 'EPAYTEST')

    @patch('requests.post')
    def test_api_initiate_khalti(self, mock_post):
        """Verify API initiation for Khalti calls Khalti API and returns payment_url and pidx."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'pidx': 'test_api_pidx_123',
            'payment_url': 'https://test-pay.khalti.com/?pidx=test_api_pidx_123'
        }
        mock_post.return_value = mock_response

        url = reverse('api_payment_initiate')
        response = self.client.post(url, {
            'appointment_id': str(self.appointment.id),
            'gateway': 'KHALTI'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['gateway'], 'KHALTI')
        self.assertEqual(response.data['pidx'], 'test_api_pidx_123')
        self.assertEqual(response.data['payment_url'], 'https://test-pay.khalti.com/?pidx=test_api_pidx_123')

    def test_api_verify_esewa_success(self):
        """Verify API verify endpoint marks eSewa payment SUCCESS and appointment PENDING."""
        payment = Payment.objects.create(
            appointment=self.appointment,
            patient=self.patient,
            gateway=Payment.Gateway.ESEWA,
            amount=800,
            status=Payment.Status.INITIATED
        )

        txn_code = "API_ESEWA_TXN_001"
        status_val = "COMPLETE"
        total_amount = "800"
        txn_uuid = str(payment.transaction_uuid)
        product_code = "EPAYTEST"
        signed_fields = "transaction_code,status,total_amount,transaction_uuid,product_code,signed_field_names"

        sig_msg = f"transaction_code={txn_code},status={status_val},total_amount={total_amount},transaction_uuid={txn_uuid},product_code={product_code},signed_field_names={signed_fields}"
        signature = EsewaPaymentService.generate_signature(sig_msg)

        payload_dict = {
            'transaction_code': txn_code,
            'status': status_val,
            'total_amount': total_amount,
            'transaction_uuid': txn_uuid,
            'product_code': product_code,
            'signed_field_names': signed_fields,
            'signature': signature
        }
        encoded_data = base64.b64encode(json.dumps(payload_dict).encode('utf-8')).decode('utf-8')

        url = reverse('api_payment_verify')
        response = self.client.post(url, {
            'gateway': 'ESEWA',
            'data': encoded_data
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.SUCCESS)
        self.assertEqual(payment.gateway_ref, txn_code)

        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, Appointment.Status.PENDING)

    def test_api_verify_esewa_invalid_signature_rejected(self):
        """Verify API verify endpoint rejects invalid or tampered eSewa payload with 400."""
        payment = Payment.objects.create(
            appointment=self.appointment,
            patient=self.patient,
            gateway=Payment.Gateway.ESEWA,
            amount=800,
            status=Payment.Status.INITIATED
        )

        payload_dict = {
            'transaction_code': 'TAMPERED_123',
            'status': 'COMPLETE',
            'total_amount': '800',
            'transaction_uuid': str(payment.transaction_uuid),
            'product_code': 'EPAYTEST',
            'signed_field_names': 'transaction_code,status,total_amount,transaction_uuid,product_code,signed_field_names',
            'signature': 'CORRUPTED_SIGNATURE'
        }
        encoded_data = base64.b64encode(json.dumps(payload_dict).encode('utf-8')).decode('utf-8')

        url = reverse('api_payment_verify')
        response = self.client.post(url, {
            'gateway': 'ESEWA',
            'data': encoded_data
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        payment.refresh_from_db()
        self.assertNotEqual(payment.status, Payment.Status.SUCCESS)

    @patch('requests.post')
    def test_api_verify_khalti_success(self, mock_post):
        """Verify API verify endpoint marks Khalti payment SUCCESS via lookup."""
        payment = Payment.objects.create(
            appointment=self.appointment,
            patient=self.patient,
            gateway=Payment.Gateway.KHALTI,
            gateway_ref='test_pidx_api_xyz',
            amount=800,
            status=Payment.Status.INITIATED
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'pidx': 'test_pidx_api_xyz',
            'total_amount': 80000,
            'status': 'Completed',
            'transaction_id': 'KHALTI_API_TXN_111'
        }
        mock_post.return_value = mock_response

        url = reverse('api_payment_verify')
        response = self.client.post(url, {
            'gateway': 'KHALTI',
            'pidx': 'test_pidx_api_xyz'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.SUCCESS)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, Appointment.Status.PENDING)

    def test_api_payment_list_and_detail(self):
        """Verify patient can list and view their payment transaction receipts."""
        payment = Payment.objects.create(
            appointment=self.appointment,
            patient=self.patient,
            gateway=Payment.Gateway.CASH_ON_ARRIVAL,
            amount=800,
            status=Payment.Status.INITIATED
        )

        # List
        list_url = reverse('api_payment_list')
        list_res = self.client.get(list_url)
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.data), 1)
        self.assertEqual(list_res.data[0]['id'], str(payment.id))

        # Detail
        detail_url = reverse('api_payment_detail', kwargs={'payment_id': payment.id})
        detail_res = self.client.get(detail_url)
        self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_res.data['amount'], '800.00')

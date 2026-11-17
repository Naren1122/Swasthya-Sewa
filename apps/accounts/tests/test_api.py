from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User

class Phase1APITests(TestCase):
    """
    Test suite verifying Phase 1 REST API Endpoints:
    - SimpleJWT Token Obtain & Refresh
    - REST API Patient Registration
    - Authenticated User Profile retrieval with Bearer token
    """

    def setUp(self):
        self.api_client = APIClient()

        # Create verified Doctor
        self.doctor = User.objects.create_user(
            email='dr.sharma@hospital.com',
            password='DoctorPassword123!',
            full_name='Dr. Ramesh Sharma',
            role=User.Role.DOCTOR
        )

        # Create test Patient
        self.patient = User.objects.create_user(
            email='patient.ram@gmail.com',
            password='PatientPassword123!',
            full_name='Ram Thapa',
            role=User.Role.PATIENT
        )

    def test_jwt_token_obtain_and_profile_access(self):
        """Verify JWT pair generation and authenticated /me endpoint access."""
        # 1. Obtain JWT Tokens
        token_response = self.api_client.post(reverse('token_obtain_pair'), {
            'email': 'dr.sharma@hospital.com',
            'password': 'DoctorPassword123!'
        })
        self.assertEqual(token_response.status_code, status.HTTP_200_OK)
        access_token = token_response.data.get('access')
        self.assertIsNotNone(access_token)

        # 2. Access /api/v1/auth/me/ with Bearer Token
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        profile_response = self.api_client.get(reverse('api_user_profile'))
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data['email'], 'dr.sharma@hospital.com')
        self.assertEqual(profile_response.data['role'], 'DOCTOR')

    def test_api_patient_registration(self):
        """Verify self-registration via REST API endpoint."""
        reg_data = {
            'full_name': 'Gita Adhikari',
            'email': 'gita.adhikari@gmail.com',
            'phone': '9801234567',
            'password': 'SecurePassword123!',
            'password_confirm': 'SecurePassword123!'
        }
        response = self.api_client.post(reverse('api_register_patient'), reg_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'gita.adhikari@gmail.com')
        self.assertEqual(response.data['role'], 'PATIENT')

    def test_api_patient_registration_rejects_blocked_domain(self):
        """Verify API rejects registration using temporary or reserved email domain."""
        reg_data = {
            'full_name': 'Test Bot',
            'email': 'bot@mailinator.com',
            'phone': '9801234567',
            'password': 'SecurePassword123!',
            'password_confirm': 'SecurePassword123!'
        }
        response = self.api_client.post(reverse('api_register_patient'), reg_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_api_patient_registration_rejects_weak_password(self):
        """Verify API rejects password missing special character or numbers."""
        reg_data = {
            'full_name': 'Test Bot',
            'email': 'valid.patient@gmail.com',
            'phone': '9801234567',
            'password': 'WeakPasswordWithoutNumberOrSpecial',
            'password_confirm': 'WeakPasswordWithoutNumberOrSpecial'
        }
        response = self.api_client.post(reverse('api_register_patient'), reg_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_api_patient_registration_rejects_duplicate_phone(self):
        """Verify API rejects registration using an already registered phone number."""
        User.objects.create_user(
            email='user.phone@hospital.com',
            password='Password123!',
            full_name='Phone User',
            phone='9801234567',
            role=User.Role.PATIENT
        )
        reg_data = {
            'full_name': 'Duplicate Phone User',
            'email': 'brandnew.email@gmail.com',
            'phone': '9801234567',
            'password': 'SecurePassword123!',
            'password_confirm': 'SecurePassword123!'
        }
        response = self.api_client.post(reverse('api_register_patient'), reg_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone', response.data)

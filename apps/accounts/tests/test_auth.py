import uuid
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from apps.accounts.models import User
from apps.accounts.web.decorators import doctor_required, patient_required
from apps.accounts.web.adapters import CustomSocialAccountAdapter
from apps.core.middleware import GlobalExceptionMiddleware

class Phase1AuthTests(TestCase):
    """
    Comprehensive test suite verifying Phase 1 Web & Auth:
    - UUIDv4 Primary Keys & Custom User model
    - Web Patient Signup & Login (CBVs)
    - Role-based redirection
    - Google OAuth Role-Pinning logic
    - Route authorization decorators
    - Smart Global Exception Middleware (HTMX vs API vs Browser)
    """

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

        # Create verified Doctor (Pre-provisioned by Admin)
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

        # Create test Admin
        self.admin = User.objects.create_superuser(
            email='admin@swasthya.com',
            password='AdminPassword123!',
            full_name='System Administrator'
        )

    # ----------------------------------------------------
    # 1. Custom User Model & UUIDv4 Tests
    # ----------------------------------------------------
    def test_user_has_valid_uuidv4_primary_key(self):
        """Verify user ID is a valid UUIDv4 instance, eliminating IDOR vulnerabilities."""
        self.assertIsInstance(self.patient.id, uuid.UUID)
        self.assertEqual(self.patient.role, User.Role.PATIENT)
        self.assertTrue(self.patient.is_patient)
        self.assertFalse(self.patient.is_doctor)

    def test_doctor_user_attributes(self):
        """Verify doctor has the DOCTOR role and helper properties work."""
        self.assertTrue(self.doctor.is_doctor)
        self.assertFalse(self.doctor.is_patient)
        self.assertEqual(str(self.doctor), "Dr. Ramesh Sharma (Doctor) - dr.sharma@hospital.com")

    # ----------------------------------------------------
    # 2. Web Signup & Login (Class-Based Views) Tests
    # ----------------------------------------------------
    def test_patient_web_signup_success(self):
        """Verify patient self-registration creates account and logs them in."""
        signup_data = {
            'full_name': 'Sita Nepali',
            'email': 'sita.nepali@gmail.com',
            'phone': '9841234567',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!'
        }
        response = self.client.post(reverse('signup'), signup_data)
        self.assertEqual(response.status_code, 302)  # Redirects to role_redirect
        
        # Verify Sita was created strictly as a PATIENT
        new_user = User.objects.get(email='sita.nepali@gmail.com')
        self.assertEqual(new_user.role, User.Role.PATIENT)
        self.assertEqual(new_user.full_name, 'Sita Nepali')
        self.assertEqual(new_user.username, 'sita.nepali@gmail.com')

        # Test a second signup immediately after to ensure unique username constraint is preserved
        signup_data_2 = {
            'full_name': 'Gopal Karki',
            'email': 'gopal.karki@gmail.com',
            'phone': '9841999999',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!'
        }
        # Log out Sita before testing second signup
        self.client.logout()
        res2 = self.client.post(reverse('signup'), signup_data_2)
        self.assertEqual(res2.status_code, 302)
        user2 = User.objects.get(email='gopal.karki@gmail.com')
        self.assertEqual(user2.username, 'gopal.karki@gmail.com')

    def test_patient_web_signup_password_mismatch(self):
        """Verify form validation catches mismatched passwords."""
        signup_data = {
            'full_name': 'Sita Nepali',
            'email': 'sita.mismatch@gmail.com',
            'phone': '9841234567',
            'password': 'PasswordOne123!',
            'password_confirm': 'PasswordTwo123!'
        }
        response = self.client.post(reverse('signup'), signup_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='sita.mismatch@gmail.com').exists())

    def test_patient_web_signup_blocked_domain_rejected(self):
        """Verify registration with disposable/reserved domain (@example.com) is rejected."""
        signup_data = {
            'full_name': 'Fake Patient',
            'email': 'patient@example.com',
            'phone': '9841234567',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!'
        }
        response = self.client.post(reverse('signup'), signup_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "is not permitted")
        self.assertFalse(User.objects.filter(email='patient@example.com').exists())

    def test_patient_web_signup_weak_password_rejected(self):
        """Verify passwords lacking uppercase, lowercase, numbers, or special chars are rejected."""
        # Missing special character
        signup_data = {
            'full_name': 'Weak Patient',
            'email': 'weak.patient@gmail.com',
            'phone': '9841234567',
            'password': 'NoSpecialChar123',
            'password_confirm': 'NoSpecialChar123'
        }
        response = self.client.post(reverse('signup'), signup_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "special character")
        self.assertFalse(User.objects.filter(email='weak.patient@gmail.com').exists())

    def test_web_login_with_valid_credentials(self):
        """Verify unified email/password login redirects to role_redirect."""
        login_data = {
            'email': 'dr.sharma@hospital.com',
            'password': 'DoctorPassword123!'
        }
        response = self.client.post(reverse('login'), login_data)
        self.assertRedirects(response, reverse('role_redirect'), target_status_code=302)

    def test_web_login_with_invalid_credentials(self):
        """Verify login rejection with incorrect credentials."""
        login_data = {
            'email': 'dr.sharma@hospital.com',
            'password': 'WrongPassword999!'
        }
        response = self.client.post(reverse('login'), login_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid email or password")

    # ----------------------------------------------------
    # 3. Post-Login Role-Based Routing Tests
    # ----------------------------------------------------
    def test_role_redirect_for_doctor(self):
        """Verify Doctor is routed to /doctor/dashboard/."""
        self.client.force_login(self.doctor)
        response = self.client.get(reverse('role_redirect'))
        self.assertRedirects(response, '/doctor/dashboard/', fetch_redirect_response=False)

    def test_role_redirect_for_patient(self):
        """Verify Patient is routed to /patient/dashboard/."""
        self.client.force_login(self.patient)
        response = self.client.get(reverse('role_redirect'))
        self.assertRedirects(response, '/patient/dashboard/', fetch_redirect_response=False)

    def test_role_redirect_for_admin(self):
        """Verify Superuser / Admin is routed to /admin/."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('role_redirect'))
        self.assertRedirects(response, '/admin/', fetch_redirect_response=False)

    def test_logout_via_post_clears_session(self):
        """Verify POST /accounts/logout/ logs out user and redirects to home."""
        self.client.force_login(self.patient)
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('home'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_via_get_clears_session(self):
        """Verify GET /accounts/logout/ does not return 405, logs out user, and redirects to home."""
        self.client.force_login(self.patient)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('home'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_patient_web_signup_duplicate_phone_rejected(self):
        """Verify registration with an existing phone number is rejected."""
        # Create user with phone 9841234567
        User.objects.create_user(
            email='existing.phone@hospital.com',
            password='ExistingPassword123!',
            full_name='Existing Phone User',
            phone='9841234567',
            role=User.Role.PATIENT
        )
        signup_data = {
            'full_name': 'New Patient Same Phone',
            'email': 'different.email@gmail.com',
            'phone': '9841234567',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!'
        }
        response = self.client.post(reverse('signup'), signup_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "account with this phone number already exists")
        self.assertFalse(User.objects.filter(email='different.email@gmail.com').exists())

    def test_patient_web_signup_duplicate_email_rejected(self):
        """Verify registration with an existing email is rejected."""
        signup_data = {
            'full_name': 'Duplicate Email User',
            'email': self.patient.email,  # patient.ram@gmail.com
            'phone': '9841999888',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!'
        }
        response = self.client.post(reverse('signup'), signup_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "account with this email address already exists")

    # ----------------------------------------------------
    # 4. Google OAuth Role-Pinning Tests
    # ----------------------------------------------------
    def test_oauth_new_user_role_pinned_to_patient(self):
        """Verify that any new Google OAuth signup is strictly assigned PATIENT role."""
        from allauth.socialaccount.models import SocialLogin
        adapter = CustomSocialAccountAdapter()
        user = User(email='new.visitor@gmail.com')
        sociallogin = SocialLogin(user=user)
        data = {'name': 'Hari Bahadur', 'email': 'new.visitor@gmail.com'}
        
        populated_user = adapter.populate_user(None, sociallogin, data)
        self.assertEqual(populated_user.role, User.Role.PATIENT)
        self.assertEqual(populated_user.full_name, 'Hari Bahadur')

    # ----------------------------------------------------
    # 5. Route Authorization Decorators Tests
    # ----------------------------------------------------
    def test_doctor_required_decorator_blocks_patient(self):
        """Verify @doctor_required throws PermissionDenied (403) when called by a Patient."""
        @doctor_required
        def dummy_doctor_view(request):
            return HttpResponse("Doctor Dashboard")

        request = self.factory.get('/doctor/dashboard/')
        request.user = self.patient
        
        with self.assertRaises(PermissionDenied):
            dummy_doctor_view(request)

    def test_doctor_required_decorator_allows_doctor(self):
        """Verify @doctor_required allows Doctor to access view."""
        @doctor_required
        def dummy_doctor_view(request):
            return HttpResponse("Doctor Dashboard")

        request = self.factory.get('/doctor/dashboard/')
        request.user = self.doctor
        response = dummy_doctor_view(request)
        self.assertEqual(response.status_code, 200)

    # ----------------------------------------------------
    # 6. Smart Global Exception Middleware Tests
    # ----------------------------------------------------
    def test_middleware_catches_htmx_exception_with_toast(self):
        """Verify middleware intercepts unhandled errors on HTMX requests and returns DaisyUI OOB Toast."""
        middleware = GlobalExceptionMiddleware(lambda r: None)
        request = self.factory.get('/some-endpoint/', HTTP_HX_REQUEST='true')
        response = middleware.process_exception(request, ValueError("Something unexpected crashed in slot calculation!"))

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 500)
        self.assertIn('hx-swap-oob="beforeend"', response.content.decode('utf-8'))
        self.assertIn("An unexpected error occurred", response.content.decode('utf-8'))

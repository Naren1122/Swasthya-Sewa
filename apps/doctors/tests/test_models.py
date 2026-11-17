from datetime import time, date
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.accounts.models import User
from apps.doctors.models import Department, DoctorProfile, DoctorSchedule, DoctorLeave

class DoctorModelTests(TestCase):
    """
    Test suite verifying Doctor domain models, validation, and collision-proof SEO slugs.
    """
    def setUp(self):
        self.dept = Department.objects.create(name='Cardiology', icon_name='heart')
        
        self.doc_user = User.objects.create_user(
            email='dr.ramesh@hospital.com',
            password='StrongPassword123!',
            full_name='Dr. Ramesh Sharma',
            role=User.Role.DOCTOR
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doc_user,
            department=self.dept,
            nmc_number='12345',
            qualifications='MBBS, MD',
            is_verified=True
        )

    def test_department_auto_slug(self):
        """Verify department automatically generates slug on creation."""
        self.assertEqual(self.dept.slug, 'cardiology')

    def test_doctor_profile_auto_slug_and_collision_suffix(self):
        """Verify doctor profile generates 'dr-ramesh-sharma' and collision adds suffix."""
        self.assertEqual(self.doctor.slug, 'dr-ramesh-sharma')

        # Create second doctor with identical name to test collision avoidance
        user2 = User.objects.create_user(
            email='dr.ramesh2@hospital.com',
            password='StrongPassword123!',
            full_name='Dr. Ramesh Sharma',
            role=User.Role.DOCTOR
        )
        doc2 = DoctorProfile.objects.create(
            user=user2,
            department=self.dept,
            nmc_number='12346',
            qualifications='MBBS',
            is_verified=True
        )
        self.assertEqual(doc2.slug, 'dr-ramesh-sharma-1')

    def test_schedule_validation_start_time_before_end_time(self):
        """Verify schedule raises ValidationError if start_time >= end_time."""
        invalid_schedule = DoctorSchedule(
            doctor=self.doctor,
            day_of_week=0,
            start_time=time(12, 0),
            end_time=time(10, 0)
        )
        with self.assertRaises(ValidationError):
            invalid_schedule.clean()

    def test_doctor_leave_creation(self):
        """Verify doctor leave model string representation and creation."""
        leave = DoctorLeave.objects.create(
            doctor=self.doctor,
            leave_date=date(2026, 12, 25),
            reason='Christmas Holiday'
        )
        self.assertIn('On Leave: 2026-12-25', str(leave))

import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import User
from apps.doctors.models import Department, DoctorProfile, DoctorSchedule, DoctorLeave

class Command(BaseCommand):
    help = "Seed realistic demo data for Phase 2: Departments, Verified Doctors, Weekly Shifts, and Leaves."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding Phase 2 Demo Data..."))

        # 1. Medical Departments
        departments_data = [
            {'name': 'Cardiology', 'icon_name': 'heart-pulse', 'description': 'Heart and cardiovascular care specialists.'},
            {'name': 'Orthopedics', 'icon_name': 'bone', 'description': 'Bones, joints, ligaments, and musculoskeletal surgery.'},
            {'name': 'Pediatrics', 'icon_name': 'baby', 'description': 'Comprehensive child health, growth, and pediatric care.'},
            {'name': 'Neurology', 'icon_name': 'brain', 'description': 'Brain, spine, and central nervous system disorders.'},
            {'name': 'Dermatology', 'icon_name': 'sparkles', 'description': 'Skin, hair, allergy, and cosmetic dermatology.'},
        ]

        depts = {}
        for d in departments_data:
            dept, _ = Department.objects.get_or_create(
                name=d['name'],
                defaults={'icon_name': d['icon_name'], 'description': d['description'], 'is_active': True}
            )
            depts[d['name']] = dept
        self.stdout.write(self.style.SUCCESS(f"✓ Verified {len(depts)} Medical Departments."))

        # 2. Doctors Data
        doctors_seed = [
            {
                'email': 'doctor.1@gmail.com',
                'full_name': 'Dr. Aarav Sharma',
                'dept': depts['Cardiology'],
                'nmc': '12890',
                'qualifications': 'MBBS, MD Cardiology (TUTH), FACC',
                'exp': 12,
                'bio': 'Senior Consultant Interventional Cardiologist with extensive clinical experience in cardiovascular diseases, angioplasty, and hypertension management.',
                'fee_phys': Decimal('800.00'),
                'fee_vid': Decimal('1000.00'),
                'shifts': [(0, datetime.time(9, 0), datetime.time(13, 0)),  # Mon
                           (1, datetime.time(9, 0), datetime.time(13, 0)),  # Tue
                           (2, datetime.time(9, 0), datetime.time(13, 0)),  # Wed
                           (3, datetime.time(9, 0), datetime.time(13, 0)),  # Thu
                           (4, datetime.time(9, 0), datetime.time(13, 0)),  # Fri
                           (6, datetime.time(10, 0), datetime.time(14, 0))], # Sun
            },
            {
                'email': 'dr.binod@hospital.com',
                'full_name': 'Dr. Binod Karki',
                'dept': depts['Orthopedics'],
                'nmc': '44332',
                'qualifications': 'MBBS, MS Orthopedics (NAMS), Fellowship in Arthroscopy',
                'exp': 9,
                'bio': 'Consultant Orthopedic and Joint Replacement Surgeon specializing in sports injuries, knee arthroscopy, fracture care, and joint pain.',
                'fee_phys': Decimal('900.00'),
                'fee_vid': Decimal('1100.00'),
                'shifts': [(0, datetime.time(14, 0), datetime.time(18, 0)),  # Mon
                           (1, datetime.time(14, 0), datetime.time(18, 0)),  # Tue
                           (2, datetime.time(14, 0), datetime.time(18, 0)),  # Wed
                           (3, datetime.time(14, 0), datetime.time(18, 0)),  # Thu
                           (4, datetime.time(14, 0), datetime.time(18, 0))], # Fri
            },
            {
                'email': 'dr.priya@hospital.com',
                'full_name': 'Dr. Priya Adhikari',
                'dept': depts['Pediatrics'],
                'nmc': '33219',
                'qualifications': 'MBBS, MD Pediatrics (BPKIHS)',
                'exp': 7,
                'bio': 'Specialist Pediatrician dedicated to infant wellness, child immunization, nutrition guidance, and adolescent healthcare.',
                'fee_phys': Decimal('750.00'),
                'fee_vid': Decimal('850.00'),
                'shifts': [(1, datetime.time(10, 0), datetime.time(15, 0)),  # Tue
                           (2, datetime.time(10, 0), datetime.time(15, 0)),  # Wed
                           (3, datetime.time(10, 0), datetime.time(15, 0)),  # Thu
                           (4, datetime.time(10, 0), datetime.time(15, 0)),  # Fri
                           (5, datetime.time(10, 0), datetime.time(13, 0))], # Sat
            },
            {
                'email': 'dr.suresh@hospital.com',
                'full_name': 'Dr. Suresh Shrestha',
                'dept': depts['Neurology'],
                'nmc': '20194',
                'qualifications': 'MBBS, MD, DM Neurology (AIIMS)',
                'exp': 15,
                'bio': 'Chief Neurologist treating migraine, epilepsy, stroke rehabilitation, movement disorders, and neuro-muscular conditions.',
                'fee_phys': Decimal('1200.00'),
                'fee_vid': Decimal('1500.00'),
                'shifts': [(0, datetime.time(11, 0), datetime.time(16, 0)),  # Mon
                           (2, datetime.time(11, 0), datetime.time(16, 0)),  # Wed
                           (4, datetime.time(11, 0), datetime.time(16, 0))], # Fri
            },
        ]

        default_password = "Doctor123!"

        for doc_item in doctors_seed:
            user, created = User.objects.get_or_create(
                email=doc_item['email'],
                defaults={
                    'username': doc_item['email'],
                    'full_name': doc_item['full_name'],
                    'role': User.Role.DOCTOR,
                    'is_active': True,
                }
            )
            # Ensure correct role & password
            user.role = User.Role.DOCTOR
            user.full_name = doc_item['full_name']
            user.set_password(default_password)
            user.save()

            # Profile
            profile, _ = DoctorProfile.objects.get_or_create(
                user=user,
                defaults={
                    'department': doc_item['dept'],
                    'nmc_number': doc_item['nmc'],
                    'qualifications': doc_item['qualifications'],
                    'experience_years': doc_item['exp'],
                    'bio': doc_item['bio'],
                    'fee_physical': doc_item['fee_phys'],
                    'fee_video': doc_item['fee_vid'],
                    'is_verified': True,
                    'is_available_for_telemed': True,
                }
            )
            profile.department = doc_item['dept']
            profile.is_verified = True
            profile.save()

            # Recurring Schedules
            DoctorSchedule.objects.filter(doctor=profile).delete()
            for day_idx, start_t, end_t in doc_item['shifts']:
                DoctorSchedule.objects.create(
                    doctor=profile,
                    day_of_week=day_idx,
                    start_time=start_t,
                    end_time=end_t,
                    slot_duration_minutes=20,
                    is_active=True
                )

            self.stdout.write(self.style.SUCCESS(f"✓ Provisioned {profile.user.full_name} ({profile.slug}) with active weekly shifts."))

        # 3. Add a Demo Leave for testing Leave Alert state (3 days from today)
        test_leave_date = timezone.localdate() + datetime.timedelta(days=3)
        binod_profile = DoctorProfile.objects.get(nmc_number='44332')
        DoctorLeave.objects.get_or_create(
            doctor=binod_profile,
            leave_date=test_leave_date,
            defaults={'reason': 'Attending Annual Orthopedic Surgical Conference'}
        )
        self.stdout.write(self.style.SUCCESS(f"✓ Created Demo Leave for {binod_profile.user.full_name} on {test_leave_date.strftime('%Y-%m-%d')} for edge-case testing."))

        self.stdout.write(self.style.SUCCESS("\nPhase 2 Demo Data Setup Successfully Finished!"))
        self.stdout.write("All doctor accounts use password: " + self.style.WARNING(default_password))

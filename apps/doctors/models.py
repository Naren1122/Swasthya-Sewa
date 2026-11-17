from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel

class Department(BaseModel):
    """
    Medical specialty / department (e.g. Cardiology, Neurology, Pediatrics).
    Categorizes doctors and powers SEO-friendly public browsing.
    """
    name = models.CharField('Department Name', max_length=100, unique=True)
    slug = models.SlugField('SEO Slug', max_length=120, unique=True, db_index=True)
    icon_name = models.CharField(
        'Lucide Icon Identifier',
        max_length=50,
        default='activity',
        help_text="Lucide icon name (e.g. heart, brain, baby, activity)"
    )
    description = models.TextField('Description', blank=True)
    is_active = models.BooleanField('Is Active', default=True, db_index=True)

    class Meta:
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Department.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class DoctorProfile(BaseModel):
    """
    Specialist clinical practitioner profile.
    Linked 1-to-1 with a User holding the DOCTOR role.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profile',
        limit_choices_to={'role': 'DOCTOR'}
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='doctors',
        help_text="Medical specialty department"
    )
    nmc_number = models.CharField(
        'NMC License Number',
        max_length=30,
        unique=True,
        db_index=True,
        help_text="Official Nepal Medical Council Registration Number"
    )
    slug = models.SlugField(
        'SEO Slug',
        max_length=160,
        unique=True,
        db_index=True,
        help_text="Public URL identifier (e.g. dr-ramesh-sharma)"
    )
    title = models.CharField(
        'Professional Title',
        max_length=80,
        default='Consultant Specialist',
        help_text="e.g. Senior Consultant Cardiologist"
    )
    qualifications = models.CharField(
        'Medical Degrees',
        max_length=200,
        help_text="e.g. MBBS, MD (Cardiology), FACC"
    )
    experience_years = models.PositiveIntegerField(
        'Years of Experience',
        default=1,
        validators=[MinValueValidator(0), MaxValueValidator(70)]
    )
    bio = models.TextField(
        'Professional Biography',
        blank=True,
        help_text="Clinical experience, background, and patient care philosophy"
    )
    fee_physical = models.DecimalField(
        'In-Person Consultation Fee (NPR)',
        max_digits=10,
        decimal_places=2,
        default=Decimal('800.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Standard hospital clinic visit fee in Nepali Rupees"
    )
    fee_video = models.DecimalField(
        'Telehealth Video Fee (NPR)',
        max_digits=10,
        decimal_places=2,
        default=Decimal('1000.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Virtual video consultation fee in Nepali Rupees"
    )
    is_verified = models.BooleanField(
        'NMC Verified by Hospital',
        default=False,
        db_index=True,
        help_text="Whether administrator has validated the doctor's credentials"
    )
    is_available_for_telemed = models.BooleanField(
        'Available for Telehealth',
        default=True,
        help_text="Accepts virtual video consultations via Jitsi Meet"
    )
    avatar = models.ImageField(
        'Doctor Photo',
        upload_to='doctors/avatars/',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Doctor Profile'
        verbose_name_plural = 'Doctor Profiles'
        ordering = ['user__full_name']

    def __str__(self):
        return f"{self.user.full_name} ({self.department.name}) - NMC #{self.nmc_number}"

    def clean(self):
        if self.user and self.user.role != 'DOCTOR':
            raise ValidationError("The associated user account must possess the DOCTOR role.")

    def save(self, *args, **kwargs):
        # Auto-generate collision-proof SEO slug: dr-firstname-lastname
        if not self.slug and self.user:
            name = (self.user.full_name or self.user.email.split('@')[0]).strip()
            # Clean leading 'Dr.' or 'Dr ' prefix if already present in full_name
            if name.lower().startswith('dr.'):
                name = name[3:].strip()
            elif name.lower().startswith('dr '):
                name = name[3:].strip()

            base_slug = slugify(f"dr-{name}")
            slug = base_slug
            counter = 1
            while DoctorProfile.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class DoctorSchedule(BaseModel):
    """
    Recurring weekly availability rules for a doctor.
    Day of week uses Python datetime convention:
    0 = Monday, 1 = Tuesday, 2 = Wednesday, 3 = Thursday,
    4 = Friday, 5 = Saturday, 6 = Sunday.
    """
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, 'Monday'
        TUESDAY = 1, 'Tuesday'
        WEDNESDAY = 2, 'Wednesday'
        THURSDAY = 3, 'Thursday'
        FRIDAY = 4, 'Friday'
        SATURDAY = 5, 'Saturday'
        SUNDAY = 6, 'Sunday'

    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    day_of_week = models.IntegerField(
        'Day of the Week',
        choices=DayOfWeek.choices,
        db_index=True
    )
    start_time = models.TimeField('Shift Start Time')
    end_time = models.TimeField('Shift End Time')
    slot_duration_minutes = models.PositiveIntegerField(
        'Slot Duration (Minutes)',
        default=20,
        validators=[MinValueValidator(5), MaxValueValidator(120)],
        help_text="Duration allocated per patient (typically 15, 20, or 30 minutes)"
    )
    is_active = models.BooleanField(
        'Is Active Shift',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Doctor Schedule'
        verbose_name_plural = 'Doctor Schedules'
        ordering = ['day_of_week', 'start_time']
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'day_of_week', 'start_time'],
                name='unique_doctor_day_shift'
            )
        ]

    def __str__(self):
        day_name = self.get_day_of_week_display()
        return f"{self.doctor.user.full_name} - {day_name} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"

    def clean(self):
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("Shift start time must be strictly earlier than end time.")


class DoctorLeave(BaseModel):
    """
    Ad-hoc / emergency leave overrides for doctors.
    If a leave record exists for a date, the slot calculation engine
    automatically marks all slots for that day as unavailable.
    """
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='leaves'
    )
    leave_date = models.DateField('Leave Date', db_index=True)
    reason = models.CharField('Reason for Leave', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Doctor Leave'
        verbose_name_plural = 'Doctor Leaves'
        ordering = ['-leave_date']
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'leave_date'],
                name='unique_doctor_leave_date'
            )
        ]

    def __str__(self):
        return f"{self.doctor.user.full_name} On Leave: {self.leave_date} ({self.reason or 'No reason specified'})"

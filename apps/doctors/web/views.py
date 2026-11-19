from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db import IntegrityError
from django.db.models import Q
from apps.accounts.web.decorators import doctor_required
from apps.doctors.models import Department, DoctorProfile, DoctorSchedule, DoctorLeave
from apps.doctors.services.slot_engine import compute_available_slots
from apps.doctors.web.forms import DoctorScheduleForm, DoctorLeaveForm

@method_decorator(doctor_required, name='dispatch')
class DoctorDashboardView(LoginRequiredMixin, View):
    """
    Authenticated Doctor Clinical Portal.
    Displays doctor profile status, weekly shifts, upcoming leaves,
    and a quick link to preview their public profile.
    """
    def get(self, request, *args, **kwargs):
        doctor = getattr(request.user, 'doctor_profile', None)

        schedules = []
        leaves = []
        pending_appointments = []
        upcoming_appointments = []
        past_appointments = []

        if doctor:
            schedules = doctor.schedules.filter(is_active=True).order_by('day_of_week', 'start_time')
            leaves = doctor.leaves.filter(leave_date__gte=timezone.localdate()).order_by('leave_date')
            try:
                from apps.appointments.models import Appointment
                pending_appointments = Appointment.objects.select_related('patient').filter(
                    doctor=doctor,
                    status=Appointment.Status.PENDING
                ).order_by('appointment_date', 'start_time')

                upcoming_appointments = Appointment.objects.select_related('patient').filter(
                    doctor=doctor,
                    status__in=[Appointment.Status.ACCEPTED, Appointment.Status.CONFIRMED],
                    appointment_date__gte=timezone.localdate()
                ).order_by('appointment_date', 'start_time')

                past_appointments = Appointment.objects.select_related('patient').filter(
                    doctor=doctor,
                    status__in=[Appointment.Status.COMPLETED, Appointment.Status.REJECTED, Appointment.Status.CANCELLED]
                ).order_by('-appointment_date', '-start_time')[:15]
            except Exception:
                pass

        context = {
            'doctor': doctor,
            'schedules': schedules,
            'leaves': leaves,
            'pending_appointments': pending_appointments,
            'upcoming_appointments': upcoming_appointments,
            'past_appointments': past_appointments,
            'today': timezone.localdate(),
            'schedule_form': DoctorScheduleForm(),
            'leave_form': DoctorLeaveForm(),
        }
        return render(request, 'doctors/dashboard.html', context)

class DoctorDirectoryView(View):
    """
    Public directory of doctors with department filtering and live HTMX search.
    """
    def get(self, request, *args, **kwargs):
        departments = Department.objects.filter(is_active=True).order_by('name')
        doctors = DoctorProfile.objects.select_related('user', 'department').filter(is_verified=True)

        selected_dept = request.GET.get('dept', '').strip()
        search_query = request.GET.get('q', '').strip()

        if selected_dept:
            doctors = doctors.filter(department__slug=selected_dept)

        if search_query:
            doctors = doctors.filter(
                Q(user__full_name__icontains=search_query) |
                Q(department__name__icontains=search_query) |
                Q(qualifications__icontains=search_query)
            )

        context = {
            'departments': departments,
            'doctors': doctors.order_by('user__full_name'),
            'selected_dept': selected_dept,
            'search_query': search_query,
        }

        # If request is from HTMX live search/filter, return partial only
        if request.headers.get('HX-Request'):
            return render(request, 'doctors/partials/_doctor_cards.html', context)

        return render(request, 'doctors/doctor_list.html', context)


class DoctorProfileDetailView(View):
    """
    Public Doctor Profile Detail View.
    Displays doctor credentials, department info, consultation fees,
    upcoming 7-day selector strip with auto-first-available-date selection,
    and the interactive HTMX calendar slot picker.
    """
    def get(self, request, slug, *args, **kwargs):
        doctor = get_object_or_404(
            DoctorProfile.objects.select_related('user', 'department').prefetch_related('schedules'),
            slug=slug,
            is_verified=True
        )

        today = timezone.localdate()

        # Build 7-day upcoming date selector strip (Today + next 6 days)
        scheduled_weekdays = set(doctor.schedules.filter(is_active=True).values_list('day_of_week', flat=True))
        doctor_leaves = set(DoctorLeave.objects.filter(
            doctor=doctor,
            leave_date__range=[today, today + timedelta(days=6)]
        ).values_list('leave_date', flat=True))

        upcoming_days = []
        first_available_date = None

        for i in range(7):
            curr_date = today + timedelta(days=i)
            is_scheduled = (curr_date.weekday() in scheduled_weekdays) and (curr_date not in doctor_leaves)
            day_label = 'Today' if i == 0 else ('Tomorrow' if i == 1 else curr_date.strftime('%a'))

            upcoming_days.append({
                'date': curr_date,
                'date_str': curr_date.isoformat(),
                'day_label': day_label,
                'day_name': curr_date.strftime('%a'),
                'day_num': curr_date.strftime('%d'),
                'month_name': curr_date.strftime('%b'),
                'is_today': i == 0,
                'is_scheduled': is_scheduled,
            })

            # Auto-detect the first upcoming day with available slots
            if first_available_date is None and is_scheduled:
                slots_check = compute_available_slots(doctor, curr_date)
                if slots_check.get('status') == 'SUCCESS' and slots_check.get('available_slots_count', 0) > 0:
                    first_available_date = curr_date

        # Default to first available date, or fallback to today
        target_date = first_available_date if first_available_date else today
        initial_slots = compute_available_slots(doctor, target_date)

        context = {
            'doctor': doctor,
            'today': today,
            'target_date': target_date,
            'upcoming_days': upcoming_days,
            'initial_slots': initial_slots,
            'schedules': doctor.schedules.filter(is_active=True).order_by('day_of_week', 'start_time'),
        }
        return render(request, 'doctors/doctor_detail.html', context)


class DoctorSlotPickerPartialView(View):
    """
    HTMX-powered Slot Availability Endpoint.
    Dynamically swaps the appointment slot grid when the patient selects a date on the calendar.
    """
    def get(self, request, slug, *args, **kwargs):
        doctor = get_object_or_404(
            DoctorProfile.objects.select_related('user', 'department'),
            slug=slug
        )

        date_str = request.GET.get('date')
        if date_str:
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                target_date = timezone.localdate()
        else:
            target_date = timezone.localdate()

        slot_data = compute_available_slots(doctor, target_date)

        context = {
            'doctor': doctor,
            'target_date': target_date,
            'slot_data': slot_data,
        }
        return render(request, 'doctors/partials/_slot_grid.html', context)


@method_decorator(doctor_required, name='dispatch')
class DoctorScheduleCreateView(LoginRequiredMixin, View):
    """
    Self-service endpoint for doctors to add a new working shift.
    """
    def post(self, request, *args, **kwargs):
        doctor = get_object_or_404(DoctorProfile, user=request.user)
        form = DoctorScheduleForm(request.POST, doctor=doctor)
        if form.is_valid():
            try:
                schedule = form.save(commit=False)
                schedule.doctor = doctor
                schedule.save()
                messages.success(request, f"Working shift for {schedule.get_day_of_week_display()} ({schedule.start_time.strftime('%I:%M %p')} – {schedule.end_time.strftime('%I:%M %p')}) added successfully.")
            except IntegrityError:
                messages.warning(request, "A shift starting at this time already exists in your weekly schedule.")
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
            for field, errs in form.errors.items():
                messages.error(request, f"{errs[0]}")
        return redirect('doctor_dashboard')


@method_decorator(doctor_required, name='dispatch')
class DoctorScheduleDeleteView(LoginRequiredMixin, View):
    """
    Self-service endpoint for doctors to remove an existing working shift.
    """
    def post(self, request, schedule_id, *args, **kwargs):
        doctor = get_object_or_404(DoctorProfile, user=request.user)
        schedule = get_object_or_404(DoctorSchedule, id=schedule_id, doctor=doctor)
        day_name = schedule.get_day_of_week_display()
        schedule.delete()
        messages.info(request, f"Working shift for {day_name} removed.")
        return redirect('doctor_dashboard')


@method_decorator(doctor_required, name='dispatch')
class DoctorLeaveCreateView(LoginRequiredMixin, View):
    """
    Self-service endpoint for doctors to declare planned or emergency leave.
    """
    def post(self, request, *args, **kwargs):
        doctor = get_object_or_404(DoctorProfile, user=request.user)
        form = DoctorLeaveForm(request.POST, doctor=doctor)
        if form.is_valid():
            try:
                leave = form.save(commit=False)
                leave.doctor = doctor
                leave.save()
                messages.success(request, f"Leave declared for {leave.leave_date.strftime('%A, %b %d, %Y')}.")
            except IntegrityError:
                messages.warning(request, f"Leave is already logged for {leave.leave_date.strftime('%b %d, %Y')}.")
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
            for field, errs in form.errors.items():
                messages.error(request, f"{errs[0]}")
        return redirect('doctor_dashboard')


@method_decorator(doctor_required, name='dispatch')
class DoctorLeaveDeleteView(LoginRequiredMixin, View):
    """
    Self-service endpoint for doctors to cancel an upcoming leave.
    """
    def post(self, request, leave_id, *args, **kwargs):
        doctor = get_object_or_404(DoctorProfile, user=request.user)
        leave = get_object_or_404(DoctorLeave, id=leave_id, doctor=doctor)
        date_str = leave.leave_date.strftime('%b %d, %Y')
        leave.delete()
        messages.info(request, f"Leave schedule for {date_str} cancelled.")
        return redirect('doctor_dashboard')


@method_decorator(doctor_required, name='dispatch')
class DoctorTelemedToggleView(LoginRequiredMixin, View):
    """
    Self-service endpoint for doctors to toggle virtual consultation acceptance.
    """
    def post(self, request, *args, **kwargs):
        doctor = get_object_or_404(DoctorProfile, user=request.user)
        doctor.is_available_for_telemed = not doctor.is_available_for_telemed
        doctor.save(update_fields=['is_available_for_telemed'])
        status_text = "now active" if doctor.is_available_for_telemed else "temporarily paused"
        messages.success(request, f"HD Video Teleconsultation is {status_text}.")
        return redirect('doctor_dashboard')


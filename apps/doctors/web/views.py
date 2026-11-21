from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db import IntegrityError
from django.db.models import Q, Count
from django.core.paginator import Paginator
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
    Supports 8-item pagination for consultation queues.
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
                ).order_by('-appointment_date', '-start_time')
            except Exception:
                pass

        # 8-Item Pagination for Queues
        upcoming_paginator = Paginator(upcoming_appointments, 8)
        upcoming_page_obj = upcoming_paginator.get_page(request.GET.get('upcoming_page', 1))

        past_paginator = Paginator(past_appointments, 8)
        past_page_obj = past_paginator.get_page(request.GET.get('past_page', 1))

        context = {
            'doctor': doctor,
            'schedules': schedules,
            'leaves': leaves,
            'pending_appointments': pending_appointments,
            'upcoming_appointments': upcoming_page_obj.object_list,
            'upcoming_page_obj': upcoming_page_obj,
            'past_appointments': past_page_obj.object_list,
            'past_page_obj': past_page_obj,
            'today': timezone.localdate(),
            'schedule_form': DoctorScheduleForm(),
            'leave_form': DoctorLeaveForm(),
        }
        return render(request, 'doctors/dashboard.html', context)


class DoctorDirectoryView(View):
    """
    Public directory of doctors with department filtering, live HTMX search,
    and 8 items per page pagination.
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

        doctors_qs = doctors.order_by('user__full_name')
        paginator = Paginator(doctors_qs, 8)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        context = {
            'departments': departments,
            'doctors': page_obj.object_list,
            'page_obj': page_obj,
            'selected_dept': selected_dept,
            'search_query': search_query,
        }

        # If request is from HTMX live search/filter, return partial only
        if request.headers.get('HX-Request'):
            return render(request, 'doctors/partials/_doctor_cards.html', context)

        return render(request, 'doctors/doctor_list.html', context)


class SpecialtyListView(View):
    """
    Public directory of medical departments & specialties with live 8-item pagination.
    """
    def get(self, request, *args, **kwargs):
        departments = Department.objects.filter(is_active=True).annotate(
            doctor_count=Count('doctors', filter=Q(doctors__is_verified=True))
        ).order_by('name')

        search_query = request.GET.get('q', '').strip()
        if search_query:
            departments = departments.filter(
                Q(name__icontains=search_query) | Q(description__icontains=search_query)
            )

        paginator = Paginator(departments, 8)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        context = {
            'page_obj': page_obj,
            'departments': page_obj.object_list,
            'search_query': search_query,
        }

        if request.headers.get('HX-Request'):
            return render(request, 'doctors/partials/_specialty_cards.html', context)

        return render(request, 'doctors/specialty_list.html', context)


class DoctorProfileDetailView(View):
    """
    Public Doctor Profile Detail View.
    Displays doctor credentials, department info, consultation fees,
    upcoming 7-day selector strip with auto-first-available-date selection,
    and the interactive HTMX calendar slot picker paginated by 8 slots per view.
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
        all_slots = initial_slots.get('slots', [])
        slot_paginator = Paginator(all_slots, 8)
        slot_page_obj = slot_paginator.get_page(1)

        context = {
            'doctor': doctor,
            'today': today,
            'target_date': target_date,
            'upcoming_days': upcoming_days,
            'initial_slots': initial_slots,
            'slot_page_obj': slot_page_obj,
            'paginated_slots': slot_page_obj.object_list,
            'schedules': doctor.schedules.filter(is_active=True).order_by('day_of_week', 'start_time'),
        }
        return render(request, 'doctors/doctor_detail.html', context)


class DoctorSlotPickerPartialView(View):
    """
    HTMX-powered Slot Availability Endpoint.
    Dynamically swaps the appointment slot grid when the patient selects a date on the calendar,
    with 8 slots per page pagination.
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
        all_slots = slot_data.get('slots', [])
        slot_paginator = Paginator(all_slots, 8)
        slot_page_number = request.GET.get('slot_page', 1)
        slot_page_obj = slot_paginator.get_page(slot_page_number)

        context = {
            'doctor': doctor,
            'target_date': target_date,
            'slot_data': slot_data,
            'slot_page_obj': slot_page_obj,
            'paginated_slots': slot_page_obj.object_list,
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
class DoctorScheduleUpdateView(LoginRequiredMixin, View):
    """
    Self-service endpoint for doctors to edit and update an existing working shift.
    """
    def post(self, request, schedule_id, *args, **kwargs):
        doctor = get_object_or_404(DoctorProfile, user=request.user)
        schedule = get_object_or_404(DoctorSchedule, id=schedule_id, doctor=doctor)

        form = DoctorScheduleForm(request.POST, instance=schedule, doctor=doctor)
        if form.is_valid():
            try:
                updated = form.save()
                messages.success(
                    request,
                    f"Working shift for {updated.get_day_of_week_display()} updated successfully ({updated.start_time.strftime('%I:%M %p')} – {updated.end_time.strftime('%I:%M %p')})."
                )
            except IntegrityError:
                messages.warning(request, "Another shift starting at this time already exists in your weekly schedule.")
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
    Idempotent: Prevents 404 crashes on duplicate clicks / race conditions.
    """
    def post(self, request, schedule_id, *args, **kwargs):
        doctor = get_object_or_404(DoctorProfile, user=request.user)

        # Security: Do not allow deleting another doctor's shift
        if DoctorSchedule.objects.filter(id=schedule_id).exclude(doctor=doctor).exists():
            raise Http404("No DoctorSchedule matches the given query.")

        schedule = DoctorSchedule.objects.filter(id=schedule_id, doctor=doctor).first()
        if not schedule:
            messages.info(request, "This working shift was already removed.")
            return redirect('doctor_dashboard')

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
    Idempotent: Prevents 404 crashes on duplicate clicks / race conditions.
    """
    def post(self, request, leave_id, *args, **kwargs):
        doctor = get_object_or_404(DoctorProfile, user=request.user)

        # Security: Do not allow deleting another doctor's leave
        if DoctorLeave.objects.filter(id=leave_id).exclude(doctor=doctor).exists():
            raise Http404("No DoctorLeave matches the given query.")

        leave = DoctorLeave.objects.filter(id=leave_id, doctor=doctor).first()
        if not leave:
            messages.info(request, "This scheduled leave was already cancelled.")
            return redirect('doctor_dashboard')

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

from django.urls import path
from apps.doctors.web.views import (
    DoctorDirectoryView,
    DoctorProfileDetailView,
    DoctorSlotPickerPartialView,
    DoctorDashboardView,
    DoctorScheduleCreateView,
    DoctorScheduleDeleteView,
    DoctorLeaveCreateView,
    DoctorLeaveDeleteView,
    DoctorTelemedToggleView,
)

urlpatterns = [
    # Doctor Dashboard & Self-Service
    path('doctor/dashboard/', DoctorDashboardView.as_view(), name='doctor_dashboard'),
    path('doctor/schedules/add/', DoctorScheduleCreateView.as_view(), name='doctor_schedule_create'),
    path('doctor/schedules/<uuid:schedule_id>/delete/', DoctorScheduleDeleteView.as_view(), name='doctor_schedule_delete'),
    path('doctor/leaves/add/', DoctorLeaveCreateView.as_view(), name='doctor_leave_create'),
    path('doctor/leaves/<uuid:leave_id>/delete/', DoctorLeaveDeleteView.as_view(), name='doctor_leave_delete'),
    path('doctor/telemed/toggle/', DoctorTelemedToggleView.as_view(), name='doctor_telemed_toggle'),

    # Public Doctor Directory
    path('doctors/', DoctorDirectoryView.as_view(), name='doctor_directory'),

    # Doctor Profile Detail (via SEO Slug)
    path('doctors/<slug:slug>/', DoctorProfileDetailView.as_view(), name='doctor_detail'),

    # HTMX Slot Grid Partial
    path('doctors/<slug:slug>/slots/', DoctorSlotPickerPartialView.as_view(), name='doctor_slots_partial'),
]

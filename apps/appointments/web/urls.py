from django.urls import path
from apps.appointments.web.views import (
    AppointmentHoldView,
    AppointmentCancelHoldView,
    AppointmentConfirmView,
    AppointmentDetailView,
    AppointmentCancelView,
    PatientBookingsView,
    DoctorAppointmentAcceptView,
    DoctorAppointmentRejectView,
    DoctorAppointmentCompleteView,
)

urlpatterns = [
    # 10-Minute Slot Hold Endpoint (HTMX / POST)
    path('appointments/hold/', AppointmentHoldView.as_view(), name='appointment_hold'),

    # Cancel / Release Hold Endpoint
    path('appointments/<uuid:appointment_id>/cancel-hold/', AppointmentCancelHoldView.as_view(), name='appointment_cancel_hold'),

    # Confirm Appointment Booking
    path('appointments/<uuid:appointment_id>/confirm/', AppointmentConfirmView.as_view(), name='appointment_confirm'),

    # View Appointment Receipt / Detail
    path('appointments/<uuid:appointment_id>/', AppointmentDetailView.as_view(), name='appointment_detail'),

    # Cancel Confirmed Appointment
    path('appointments/<uuid:appointment_id>/cancel/', AppointmentCancelView.as_view(), name='appointment_cancel'),

    # Doctor Actions: Accept, Reject, Complete
    path('appointments/<uuid:appointment_id>/accept/', DoctorAppointmentAcceptView.as_view(), name='doctor_appointment_accept'),
    path('appointments/<uuid:appointment_id>/reject/', DoctorAppointmentRejectView.as_view(), name='doctor_appointment_reject'),
    path('appointments/<uuid:appointment_id>/complete/', DoctorAppointmentCompleteView.as_view(), name='doctor_appointment_complete'),

    # Patient Personal Consultations List
    path('appointments/my-bookings/', PatientBookingsView.as_view(), name='patient_bookings'),
]

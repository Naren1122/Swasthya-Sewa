from django.urls import path
from apps.appointments.api.views import (
    AppointmentHoldAPIView,
    AppointmentConfirmAPIView,
    AppointmentCancelHoldAPIView,
    AppointmentCancelAPIView,
    PatientAppointmentListAPIView,
    AppointmentDetailAPIView,
)

urlpatterns = [
    # 10-Minute Slot Hold Endpoint (POST)
    path('appointments/hold/', AppointmentHoldAPIView.as_view(), name='api_appointment_hold'),

    # Confirm Active Hold (POST)
    path('appointments/<uuid:appointment_id>/confirm/', AppointmentConfirmAPIView.as_view(), name='api_appointment_confirm'),

    # Release Slot Hold (POST)
    path('appointments/<uuid:appointment_id>/cancel-hold/', AppointmentCancelHoldAPIView.as_view(), name='api_appointment_cancel_hold'),

    # Cancel Confirmed Appointment (POST)
    path('appointments/<uuid:appointment_id>/cancel/', AppointmentCancelAPIView.as_view(), name='api_appointment_cancel'),

    # Patient's Bookings List (GET)
    path('appointments/my-bookings/', PatientAppointmentListAPIView.as_view(), name='api_patient_bookings'),

    # Appointment Detail / Receipt (GET)
    path('appointments/<uuid:appointment_id>/', AppointmentDetailAPIView.as_view(), name='api_appointment_detail'),
]

from django.urls import path
from apps.doctors.api.views import (
    DepartmentListAPIView,
    DoctorListAPIView,
    DoctorDetailAPIView,
    DoctorSlotAvailabilityAPIView,
)

urlpatterns = [
    # Departments
    path('departments/', DepartmentListAPIView.as_view(), name='api_department_list'),

    # Doctors Directory & Profile
    path('doctors/', DoctorListAPIView.as_view(), name='api_doctor_list'),
    path('doctors/<slug:slug>/', DoctorDetailAPIView.as_view(), name='api_doctor_detail'),

    # Dynamic Slot Calculation Endpoint
    path('doctors/<slug:slug>/slots/', DoctorSlotAvailabilityAPIView.as_view(), name='api_doctor_slots'),
]

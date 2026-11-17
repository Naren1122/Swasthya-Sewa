from datetime import date
from django.db import models
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from apps.doctors.models import Department, DoctorProfile
from apps.doctors.api.serializers import (
    DepartmentSerializer,
    DoctorListSerializer,
    DoctorDetailSerializer,
)
from apps.doctors.services.slot_engine import compute_available_slots

@extend_schema(
    tags=['Doctors & Departments'],
    summary="List all active medical departments",
    description="Returns all active hospital clinical departments (e.g. Cardiology, Neurology, Pediatrics)."
)
class DepartmentListAPIView(generics.ListAPIView):
    """
    Public API endpoint to browse hospital departments.
    """
    queryset = Department.objects.filter(is_active=True).order_by('name')
    serializer_class = DepartmentSerializer
    permission_classes = [AllowAny]


@extend_schema(
    tags=['Doctors & Departments'],
    summary="List and filter medical doctors",
    description="Public endpoint to list verified doctors with optional filtering by department slug, telemed availability, or search query.",
    parameters=[
        OpenApiParameter(name='department', description='Filter by department slug (e.g. cardiology)', required=False, type=str),
        OpenApiParameter(name='telemed', description='Filter by teleconsultation support (true/false)', required=False, type=bool),
        OpenApiParameter(name='search', description='Search doctor by name or NMC number', required=False, type=str),
    ]
)
class DoctorListAPIView(generics.ListAPIView):
    """
    Public API endpoint to list and search doctors.
    Uses select_related('user', 'department') to eliminate N+1 database queries.
    """
    serializer_class = DoctorListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = DoctorProfile.objects.select_related('user', 'department').filter(is_verified=True)

        department_slug = self.request.query_params.get('department')
        if department_slug:
            queryset = queryset.filter(department__slug=department_slug)

        telemed = self.request.query_params.get('telemed')
        if telemed is not None:
            if telemed.lower() in ['true', '1']:
                queryset = queryset.filter(is_available_for_telemed=True)
            elif telemed.lower() in ['false', '0']:
                queryset = queryset.filter(is_available_for_telemed=False)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(user__full_name__icontains=search) |
                models.Q(nmc_number__icontains=search)
            )

        return queryset.order_by('user__full_name')


@extend_schema(
    tags=['Doctors & Departments'],
    summary="Retrieve doctor profile by SEO slug",
    description="Returns detailed profile information for a doctor including department, degrees, fees, and active weekly schedules."
)
class DoctorDetailAPIView(generics.RetrieveAPIView):
    """
    Public API endpoint to view a doctor's detailed profile using their unique SEO slug.
    """
    queryset = DoctorProfile.objects.select_related('user', 'department').prefetch_related('schedules')
    serializer_class = DoctorDetailSerializer
    lookup_field = 'slug'
    permission_classes = [AllowAny]


@extend_schema(
    tags=['Doctors & Departments'],
    summary="Compute dynamic appointment slots for a doctor",
    description="Calculates real-time slot availability for a doctor on a specific date (YYYY-MM-DD), taking into account weekly shifts, leaves, and existing bookings.",
    parameters=[
        OpenApiParameter(name='date', description='Target appointment date (format: YYYY-MM-DD). Defaults to today.', required=False, type=str),
    ]
)
class DoctorSlotAvailabilityAPIView(APIView):
    """
    Dynamic Slot Calculation API Endpoint.
    Powers both mobile clients and frontend calendar slot pickers.
    """
    permission_classes = [AllowAny]

    def get(self, request, slug, *args, **kwargs):
        doctor = generics.get_object_or_404(
            DoctorProfile.objects.select_related('user', 'department'),
            slug=slug
        )

        date_param = request.query_params.get('date')
        if date_param:
            try:
                target_date = date.fromisoformat(date_param)
            except ValueError:
                return Response(
                    {'error': "Invalid date format. Please provide a date in 'YYYY-MM-DD' ISO format."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            target_date = timezone.localdate()

        # Execute pure Python slot engine service
        slot_data = compute_available_slots(doctor, target_date)
        return Response(slot_data, status=status.HTTP_200_OK)

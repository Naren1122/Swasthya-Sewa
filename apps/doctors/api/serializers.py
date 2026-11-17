from rest_framework import serializers
from apps.doctors.models import Department, DoctorProfile, DoctorSchedule, DoctorLeave

class DepartmentSerializer(serializers.ModelSerializer):
    """
    Serializer for medical specialty departments.
    """
    doctors_count = serializers.IntegerField(source='doctors.count', read_only=True)

    class Meta:
        model = Department
        fields = ['id', 'name', 'slug', 'icon_name', 'description', 'doctors_count']


class DoctorScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for recurring weekly working shifts.
    """
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = DoctorSchedule
        fields = [
            'id',
            'day_of_week',
            'day_name',
            'start_time',
            'end_time',
            'slot_duration_minutes',
            'is_active'
        ]


class DoctorListSerializer(serializers.ModelSerializer):
    """
    High-performance lightweight serializer for public doctor directory.
    Uses select_related to eliminate N+1 queries.
    """
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_slug = serializers.CharField(source='department.slug', read_only=True)

    class Meta:
        model = DoctorProfile
        fields = [
            'id',
            'full_name',
            'slug',
            'department_name',
            'department_slug',
            'title',
            'qualifications',
            'experience_years',
            'nmc_number',
            'fee_physical',
            'fee_video',
            'is_verified',
            'is_available_for_telemed',
            'avatar',
        ]


class DoctorDetailSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for detailed doctor profile view.
    Includes full biography, department details, and active recurring schedules.
    """
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    department = DepartmentSerializer(read_only=True)
    schedules = serializers.SerializerMethodField()

    class Meta:
        model = DoctorProfile
        fields = [
            'id',
            'full_name',
            'email',
            'slug',
            'department',
            'nmc_number',
            'title',
            'qualifications',
            'experience_years',
            'bio',
            'fee_physical',
            'fee_video',
            'is_verified',
            'is_available_for_telemed',
            'avatar',
            'schedules',
            'created_at',
        ]

    def get_schedules(self, obj):
        active_shifts = obj.schedules.filter(is_active=True).order_by('day_of_week', 'start_time')
        return DoctorScheduleSerializer(active_shifts, many=True).data

from django.contrib import admin
from apps.doctors.models import Department, DoctorProfile, DoctorSchedule, DoctorLeave

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


class DoctorScheduleInline(admin.TabularInline):
    model = DoctorSchedule
    extra = 1
    fields = ('day_of_week', 'start_time', 'end_time', 'slot_duration_minutes', 'is_active')


class DoctorLeaveInline(admin.TabularInline):
    model = DoctorLeave
    extra = 0
    fields = ('leave_date', 'reason')


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = (
        'get_full_name',
        'department',
        'nmc_number',
        'fee_physical',
        'fee_video',
        'is_verified',
        'is_available_for_telemed',
        'slug'
    )
    list_filter = ('department', 'is_verified', 'is_available_for_telemed')
    search_fields = ('user__full_name', 'user__email', 'nmc_number', 'qualifications')
    readonly_fields = ('slug', 'created_at', 'updated_at')
    inlines = [DoctorScheduleInline, DoctorLeaveInline]

    fieldsets = (
        ('Doctor Account & Identity', {
            'fields': ('user', 'department', 'nmc_number', 'slug', 'is_verified')
        }),
        ('Professional Credentials', {
            'fields': ('title', 'qualifications', 'experience_years', 'bio', 'avatar')
        }),
        ('Consultation Fees (NPR)', {
            'fields': ('fee_physical', 'fee_video', 'is_available_for_telemed')
        }),
        ('Audit Metadata', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_full_name(self, obj):
        return obj.user.full_name
    get_full_name.short_description = 'Doctor Name'
    get_full_name.admin_order_field = 'user__full_name'


@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'get_day_name', 'start_time', 'end_time', 'slot_duration_minutes', 'is_active')
    list_filter = ('day_of_week', 'is_active')
    search_fields = ('doctor__user__full_name', 'doctor__nmc_number')

    def get_day_name(self, obj):
        return obj.get_day_of_week_display()
    get_day_name.short_description = 'Day'


@admin.register(DoctorLeave)
class DoctorLeaveAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'leave_date', 'reason', 'created_at')
    list_filter = ('leave_date',)
    search_fields = ('doctor__user__full_name', 'reason')

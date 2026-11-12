from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.exceptions import ValidationError
from .models import PatientProfile, StaffProfile, User


class CustomUserCreationForm(UserCreationForm):
    """Form used to create new users in Django Admin."""

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'role')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError('A user with this email already exists.')
        return email


class CustomUserChangeForm(UserChangeForm):
    """Form used to edit existing users in Django Admin."""

    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for the custom User model.
    Uses custom forms to avoid default username field assumptions.
    """
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = ('email', 'full_name', 'role', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Role & Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    """Admin configuration for Patient profiles with optimized queries."""
    list_display = (
        'patient_number',
        'user',
        'gender',
        'blood_group',
        'emergency_contact_name',
        'emergency_contact_phone',
        'created_at',
    )
    list_filter = ('gender', 'blood_group', 'created_at')
    search_fields = (
        'patient_number',
        'user__email',
        'user__first_name',
        'user__last_name',
        'emergency_contact_name',
        'emergency_contact_phone',
    )
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('user',)
    raw_id_fields = ('user',)


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    """Admin configuration for Staff profiles with optimized queries."""
    list_display = (
        'employee_id',
        'user',
        'department_name',
        'designation',
        'license_number',
        'is_active',
        'created_at',
    )
    list_filter = ('user__is_active', 'department_name', 'designation', 'created_at')
    search_fields = (
        'employee_id',
        'user__email',
        'user__first_name',
        'user__last_name',
        'department_name',
        'designation',
        'license_number',
    )
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('user',)
    raw_id_fields = ('user',)

    @admin.display(boolean=True, description='Active')
    def is_active(self, obj):
        return obj.user.is_active

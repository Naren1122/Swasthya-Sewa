from rest_framework.permissions import BasePermission
from apps.accounts.models import User

class IsDoctorUser(BasePermission):
    """
    DRF Permission: Allows access only to authenticated users with the DOCTOR role.
    Superusers automatically pass.
    """
    message = "Access restricted to certified Doctors only."

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_doctor or request.user.is_superuser)
        )


class IsPatientUser(BasePermission):
    """
    DRF Permission: Allows access only to authenticated users with the PATIENT role.
    Superusers automatically pass.
    """
    message = "Access restricted to Patients only."

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_patient or request.user.is_superuser)
        )


class IsAdminUser(BasePermission):
    """
    DRF Permission: Allows access only to platform/hospital administrators and superusers.
    """
    message = "Access restricted to Administrators only."

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.is_admin_user
        )

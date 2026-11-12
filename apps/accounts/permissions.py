from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from rest_framework.permissions import BasePermission
from .models import Role


class IsAuthenticatedActive(BasePermission):
    """Allows access only to authenticated and active users."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active)


class IsAdmin(BasePermission):
    """Allows access only to hospital administrators or superusers."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.is_admin
        )


class IsDoctor(BasePermission):
    """Allows access to doctors (and administrators)."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and (request.user.is_doctor or request.user.is_admin)
        )


class IsReceptionist(BasePermission):
    """Allows access to receptionist/front desk staff (and administrators)."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and (request.user.is_receptionist or request.user.is_admin)
        )


class IsPatient(BasePermission):
    """Allows access to patients."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.is_patient
        )


class IsHospitalStaff(BasePermission):
    """
    Allows access to any hospital staff member:
    Admin, Doctor, Receptionist, Nurse, Lab Tech, Pharmacist, Billing.
    """

    STAFF_ROLES = {
        Role.ADMIN,
        Role.RECEPTIONIST,
        Role.DOCTOR,
        Role.NURSE,
        Role.LAB_TECHNICIAN,
        Role.PHARMACIST,
        Role.BILLING,
    }

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and (request.user.role in self.STAFF_ROLES or request.user.is_staff)
        )


class IsSelfOrAdmin(BasePermission):
    """
    Object-level permission allowing users to access only their own object,
    while hospital administrators retain oversight access.
    Adheres strictly to FR-02 (Anti-IDOR / object-level check).
    """

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False

        if request.user.is_admin:
            return True

        # Check if the target object is the user directly
        if obj == request.user:
            return True

        # Check if the target object has a `user` foreign key/one-to-one
        if hasattr(obj, 'user') and obj.user == request.user:
            return True

        return False


def role_required(*allowed_roles):
    """
    View decorator for Django/HTMX views enforcing role-based access control.
    Raises PermissionDenied (403) or redirects unauthenticated users to login.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')

            if not request.user.is_active:
                raise PermissionDenied('Your account has been deactivated.')

            if request.user.is_admin or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            raise PermissionDenied('You do not have permission to access this resource.')

        return _wrapped_view
    return decorator


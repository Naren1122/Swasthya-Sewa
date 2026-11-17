from functools import wraps
from typing import Callable, Iterable
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from apps.accounts.models import User

def role_required(allowed_roles: Iterable[str]) -> Callable:
    """
    Decorator for views that checks whether the logged-in user has
    one of the allowed roles (e.g. 'PATIENT', 'DOCTOR', 'ADMIN').
    
    Behavior:
    1. If user is not authenticated -> redirects to login page with `?next=`.
    2. If user is authenticated but lacks required role -> raises HTTP 403 (PermissionDenied).
    3. If user has required role -> executes the view.
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, "Please sign in to access this page.")
                return redirect(f"/accounts/login/?next={request.path}")

            # Superusers always bypass role checks
            if request.user.is_superuser or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            # Access Denied
            raise PermissionDenied("You do not have permission to access this healthcare portal.")
        return _wrapped_view
    return decorator


# Convenience Shortcut Decorators
doctor_required = role_required([User.Role.DOCTOR])
patient_required = role_required([User.Role.PATIENT])
admin_required = role_required([User.Role.ADMIN])

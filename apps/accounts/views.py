from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST
from django_htmx.http import HttpResponseClientRedirect

from apps.audit.models import AuditAction
from apps.audit.services import log_audit_event

from .forms import LoginForm, PatientRegistrationForm
from .services import (
    authenticate_and_login_user,
    get_redirect_url_for_user,
    logout_user,
    register_patient,
)


def _safe_next(request) -> str | None:
    """
    Validates redirect target to prevent open redirect vulnerabilities.
    Ensures destination belongs to an allowed host and matches scheme requirements.
    """
    target = request.GET.get('next') or request.POST.get('next')
    if target and url_has_allowed_host_and_scheme(
        target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return target
    return None


def _redirect_or_htmx(request, destination: str):
    """Returns an HTMX client-side redirect or standard HTTP redirect."""
    if getattr(request, 'htmx', False):
        return HttpResponseClientRedirect(destination)
    return redirect(destination)


@sensitive_post_parameters('password')
@never_cache
def login_view(request):
    """
    Handles user authentication.
    Supports both standard POST submissions and HTMX partial requests.
    Validates redirect destinations against open-redirect attacks.
    """
    if request.user.is_authenticated:
        return redirect(get_redirect_url_for_user(request.user))

    redirect_target = _safe_next(request)

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user = authenticate_and_login_user(request, email=email, password=password)
                log_audit_event(
                    action=AuditAction.LOGIN_SUCCESS,
                    actor=user,
                    request=request,
                    description=f"User {user.email} authenticated successfully.",
                )
                destination = redirect_target or get_redirect_url_for_user(user)
                return _redirect_or_htmx(request, destination)
            except ValidationError as exc:
                log_audit_event(
                    action=AuditAction.LOGIN_FAILED,
                    request=request,
                    description=f"Failed login attempt for {email}.",
                    extra_data={'attempted_email': email},
                )
                form.add_error(None, exc)
    else:
        form = LoginForm()

    context = {
        'form': form,
        'next': redirect_target,
    }

    if getattr(request, 'htmx', False) and request.method == 'POST':
        return render(request, 'accounts/partials/_login_form.html', context)

    return render(request, 'accounts/login.html', context)


@require_POST
def logout_view(request):
    """
    Logs out the authenticated user.
    Requires POST to prevent cross-origin image-based CSRF logout attacks.
    """
    if request.user.is_authenticated:
        log_audit_event(
            action=AuditAction.LOGOUT,
            actor=request.user,
            request=request,
            description=f"User {request.user.email} logged out.",
        )
        logout_user(request)
        messages.info(request, 'You have been successfully logged out.')
    return redirect('accounts:login')


@sensitive_post_parameters('password', 'confirm_password')
@never_cache
def register_patient_view(request):
    """
    Handles self-service registration for new patients.
    Complies with PRD FR-01, FR-03, and US-01.
    """
    if request.user.is_authenticated:
        return redirect(get_redirect_url_for_user(request.user))

    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                user, profile = register_patient(
                    email=data['email'],
                    password=data['password'],
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    phone_number=data.get('phone_number', ''),
                    date_of_birth=data.get('date_of_birth'),
                    gender=data.get('gender', ''),
                    address=data.get('address', ''),
                    emergency_contact_name=data.get('emergency_contact_name', ''),
                    emergency_contact_phone=data.get('emergency_contact_phone', ''),
                    emergency_contact_relation=data.get('emergency_contact_relation', ''),
                )

                # Log in directly with the newly created user (prevents double password hashing)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')

                log_audit_event(
                    action=AuditAction.USER_REGISTERED,
                    actor=user,
                    request=request,
                    target_type='PatientProfile',
                    target_id=profile.patient_number,
                    description=f"Patient {user.full_name} registered with MRN {profile.patient_number}.",
                )

                messages.success(
                    request,
                    f"Welcome to MediCore, {user.first_name}! Your patient number is {profile.patient_number}.",
                )

                destination = get_redirect_url_for_user(user)
                return _redirect_or_htmx(request, destination)

            except ValidationError as exc:
                form.add_error(None, exc)
    else:
        form = PatientRegistrationForm()

    context = {'form': form}

    if getattr(request, 'htmx', False) and request.method == 'POST':
        return render(request, 'accounts/partials/_register_form.html', context)

    return render(request, 'accounts/register.html', context)


@login_required
def dashboard_router_view(request):
    """Directs authenticated users to their assigned role workspace."""
    return redirect(get_redirect_url_for_user(request.user))

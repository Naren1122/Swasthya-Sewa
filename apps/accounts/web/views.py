from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, logout
from django.contrib import messages
from apps.accounts.models import User
from apps.accounts.web.forms import PatientSignupForm, CustomLoginForm

class PatientSignUpView(CreateView):
    """
    Class-Based View for Patient self-registration.
    Automatically logs in the patient upon successful signup.
    """
    model = User
    form_class = PatientSignupForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('role_redirect')

    def dispatch(self, request, *args, **kwargs):
        # Redirect already authenticated users to their dashboard
        if request.user.is_authenticated:
            return redirect('role_redirect')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        # Log the patient in immediately with our custom backend
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(self.request, f"Welcome to Swasthya-Sewa, {user.full_name}! Your account is ready.")
        return response


class CustomLoginView(LoginView):
    """
    Class-Based View for unified Patient and Doctor login.
    Supports email/password authentication alongside the Google OAuth button.
    """
    form_class = CustomLoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        # Respect safe ?next=/target/ url if provided
        next_url = self.request.GET.get('next')
        if next_url and next_url.startswith('/'):
            return next_url
        return reverse_lazy('role_redirect')

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().full_name}!")
        return super().form_valid(form)


class CustomLogoutView(View):
    """
    Class-Based View for user logout.
    Handles both POST (standard secure practice) and GET (frictionless link / URL bar navigation)
    without raising 405 Method Not Allowed in Django 5.
    Flushes user session and redirects to 'home' with a friendly confirmation message.
    """
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user_name = request.user.full_name or request.user.email
            logout(request)
            messages.info(request, f"You have been successfully signed out. See you soon, {user_name}!")
        return redirect('home')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class RoleRedirectView(LoginRequiredMixin, View):
    """
    Class-Based View for smart post-login role-based routing:
    - ADMIN / Superuser -> /admin/
    - DOCTOR -> doctor_dashboard (/doctor/dashboard/)
    - PATIENT -> patient_dashboard (/patient/dashboard/)
    """
    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_superuser or user.role == User.Role.ADMIN:
            return redirect('/admin/')
        elif user.role == User.Role.DOCTOR:
            return redirect('doctor_dashboard')
        else:
            return redirect('patient_dashboard')


class PatientDashboardView(LoginRequiredMixin, View):
    """
    Authenticated Patient Portal.
    Displays patient profile, upcoming medical appointments, and quick booking actions.
    """
    def get(self, request, *args, **kwargs):
        context = {
            'appointments': [],
        }
        return render(request, 'accounts/dashboard.html', context)


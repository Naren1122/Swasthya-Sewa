import re
from django import forms
from django.contrib.auth import authenticate
from apps.accounts.models import User
from apps.accounts.validators import validate_email_domain, validate_password_complexity

class PatientSignupForm(forms.ModelForm):
    """
    Self-service registration form for Patients.
    Includes clean DaisyUI / Tailwind styling, domain validation, and strict password complexity.
    """
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'class': 'input input-bordered w-full rounded-xl text-sm focus:input-primary'
        }),
        min_length=8,
        help_text="Min. 8 characters with uppercase, lowercase, number & special symbol."
    )
    password_confirm = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'class': 'input input-bordered w-full rounded-xl text-sm focus:input-primary'
        })
    )

    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone', 'password']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'placeholder': 'e.g. Ramesh Thapa',
                'class': 'input input-bordered w-full rounded-xl text-sm focus:input-primary'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'name@example.com',
                'class': 'input input-bordered w-full rounded-xl text-sm focus:input-primary'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'e.g. 98XXXXXXXX',
                'class': 'input input-bordered w-full rounded-xl text-sm focus:input-primary'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        validate_email_domain(email)
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists. Please sign in.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise forms.ValidationError("Phone number is required for appointment alerts.")

        clean_number = re.sub(r'[\s\-+]', '', phone)
        if clean_number.startswith('977'):
            clean_number = clean_number[3:]

        # Validate standard 10-digit Nepali mobile number (NTC/Ncell: 98XXXXXXXX or 97XXXXXXXX)
        if not re.match(r'^9[78]\d{8}$', clean_number):
            raise forms.ValidationError("Please enter a valid 10-digit Nepali mobile number (e.g., 98XXXXXXXX).")

        if User.objects.filter(phone=clean_number).exists():
            raise forms.ValidationError("An account with this phone number already exists.")

        return clean_number

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            validate_password_complexity(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Passwords do not match. Please try again.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = User.Role.PATIENT  # Enforce patient role for self-registration
        user.username = user.email     # Synchronize username with email
        if commit:
            user.save()
        return user


class CustomLoginForm(forms.Form):
    """
    Unified Login Form for both Patients and Doctors using Email and Password.
    """
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'placeholder': 'name@example.com',
            'class': 'input input-bordered w-full rounded-xl text-sm focus:input-primary',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'class': 'input input-bordered w-full rounded-xl text-sm focus:input-primary',
            'autocomplete': 'current-password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email', '').lower().strip()
        password = cleaned_data.get('password')

        if email and password:
            self.user = authenticate(self.request, username=email, password=password)
            if not self.user:
                raise forms.ValidationError("Invalid email or password. Please verify your credentials.")
            if not self.user.is_active:
                raise forms.ValidationError("This account has been deactivated. Please contact support.")

        return cleaned_data

    def get_user(self):
        return getattr(self, 'user', None)

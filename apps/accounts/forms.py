from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Gender, User


class TailwindFormMixin:
    """Applies uniform DaisyUI and Tailwind CSS classes to form widgets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs.setdefault('class', 'select select-bordered w-full')
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault('class', 'textarea textarea-bordered w-full')
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', 'checkbox checkbox-primary')
            else:
                widget.attrs.setdefault('class', 'input input-bordered w-full')


class LoginForm(TailwindFormMixin, forms.Form):
    """
    Form for user authentication.
    Accepts email and password.
    """
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'placeholder': 'name@hospital.com',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
        }),
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '')
        return email.strip().lower()


class PatientRegistrationForm(TailwindFormMixin, forms.Form):
    """
    Form for self-service patient onboarding.
    Validates account credentials alongside demographic intake.
    """
    # Account Credentials
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'placeholder': 'your.email@example.com',
        }),
    )
    first_name = forms.CharField(
        max_length=150,
        label='First Name',
        widget=forms.TextInput(attrs={
            'placeholder': 'First name',
        }),
    )
    last_name = forms.CharField(
        max_length=150,
        label='Last Name',
        widget=forms.TextInput(attrs={
            'placeholder': 'Last name',
        }),
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        label='Phone Number',
        widget=forms.TextInput(attrs={
            'placeholder': '98XXXXXXXX',
        }),
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter a strong password',
        }),
    )
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Repeat your password',
        }),
    )

    # Patient Demographics
    date_of_birth = forms.DateField(
        required=False,
        label='Date of Birth',
        widget=forms.DateInput(attrs={
            'type': 'date',
        }),
    )
    gender = forms.ChoiceField(
        choices=[('', 'Select Gender')] + list(Gender.choices),
        required=False,
        label='Gender',
    )
    address = forms.CharField(
        required=False,
        label='Residential Address',
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Municipality, Ward, District',
        }),
    )

    # Emergency Contact
    emergency_contact_name = forms.CharField(
        max_length=150,
        required=False,
        label='Emergency Contact Name',
        widget=forms.TextInput(attrs={
            'placeholder': 'Relative or guardian name',
        }),
    )
    emergency_contact_phone = forms.CharField(
        max_length=20,
        required=False,
        label='Emergency Contact Phone',
        widget=forms.TextInput(attrs={
            'placeholder': '98XXXXXXXX',
        }),
    )
    emergency_contact_relation = forms.CharField(
        max_length=50,
        required=False,
        label='Relationship',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. Spouse, Parent, Sibling',
        }),
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError('An account with this email address already exists.')
        return email

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > timezone.localdate():
            raise ValidationError('Date of birth cannot be in the future.')
        return dob

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password:
            try:
                validate_password(password)
            except ValidationError as exc:
                self.add_error('password', exc)

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')

        return cleaned_data

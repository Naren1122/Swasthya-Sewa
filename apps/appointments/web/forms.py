import uuid
from django import forms
from django.utils import timezone
from apps.appointments.models import Appointment

class AppointmentHoldForm(forms.Form):
    """
    Form validating the 10-minute slot hold request.
    Submitted via HTMX when a patient clicks an available slot.
    """
    doctor_id = forms.UUIDField(required=True)
    date = forms.DateField(required=True)
    time = forms.TimeField(required=True)
    consultation_type = forms.ChoiceField(
        choices=Appointment.ConsultationType.choices,
        initial=Appointment.ConsultationType.PHYSICAL,
        required=False
    )
    patient_notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Briefly describe your symptoms or reason for consultation (optional)...',
            'rows': 2,
            'class': 'textarea textarea-bordered w-full rounded-2xl text-xs sm:text-sm focus:textarea-primary bg-white text-slate-900'
        })
    )

    def clean_date(self):
        target_date = self.cleaned_data.get('date')
        if target_date and target_date < timezone.localdate():
            raise forms.ValidationError("Cannot reserve an appointment date in the past.")
        return target_date


class AppointmentConfirmForm(forms.Form):
    """
    Form validating the final appointment confirmation and symptom notes.
    """
    consultation_type = forms.ChoiceField(
        choices=Appointment.ConsultationType.choices,
        required=True
    )
    patient_notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Briefly describe your symptoms or reason for visit...',
            'rows': 3,
            'class': 'textarea textarea-bordered w-full rounded-2xl text-xs sm:text-sm focus:textarea-primary bg-white text-slate-900 border-slate-300'
        })
    )


from django import forms
from django.utils import timezone
from apps.doctors.models import DoctorSchedule, DoctorLeave

class DoctorScheduleForm(forms.ModelForm):
    """
    Doctor Self-Service form to configure weekly shift hours.
    Includes smart conflict & overlap detection.
    """
    def __init__(self, *args, **kwargs):
        self.doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = DoctorSchedule
        fields = ['day_of_week', 'start_time', 'end_time', 'slot_duration_minutes']
        widgets = {
            'day_of_week': forms.Select(attrs={
                'class': 'select select-bordered w-full rounded-xl text-sm focus:select-primary bg-white text-slate-900'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'input input-bordered w-full rounded-xl text-sm focus:input-primary bg-white text-slate-900'
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'input input-bordered w-full rounded-xl text-sm focus:input-primary bg-white text-slate-900'
            }),
            'slot_duration_minutes': forms.Select(
                choices=[
                    (15, '15 Minutes (Quick follow-up)'),
                    (20, '20 Minutes (Standard clinical consultation)'),
                    (30, '30 Minutes (Comprehensive specialty review)'),
                    (45, '45 Minutes (Psychiatry / In-depth assessment)'),
                    (60, '60 Minutes (Extended procedure)'),
                ],
                attrs={
                    'class': 'select select-bordered w-full rounded-xl text-sm focus:select-primary bg-white text-slate-900'
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        day_of_week = cleaned_data.get('day_of_week')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            if start_time >= end_time:
                self.add_error('end_time', "Shift end time must be after start time.")

            # Validate duplicates and overlapping intervals for this doctor
            if self.doctor is not None and day_of_week is not None:
                qs = DoctorSchedule.objects.filter(doctor=self.doctor, day_of_week=day_of_week)
                if self.instance and self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)

                # 1. Exact duplicate start_time check (prevents DB unique constraint violation)
                if qs.filter(start_time=start_time).exists():
                    self.add_error(
                        'start_time',
                        f"You already have a shift starting at {start_time.strftime('%I:%M %p')} on this day."
                    )
                # 2. Interval overlap check: existing.start < new.end AND existing.end > new.start
                elif qs.filter(start_time__lt=end_time, end_time__gt=start_time).exists():
                    overlapping = qs.filter(start_time__lt=end_time, end_time__gt=start_time).first()
                    day_name = dict(DoctorSchedule.DayOfWeek.choices).get(day_of_week, "this day")
                    self.add_error(
                        None,
                        f"This shift conflicts with your existing {day_name} shift ({overlapping.start_time.strftime('%I:%M %p')} – {overlapping.end_time.strftime('%I:%M %p')}). Please choose a non-overlapping time interval."
                    )

        return cleaned_data


class DoctorLeaveForm(forms.ModelForm):
    """
    Doctor Self-Service form to declare planned or emergency leave.
    """
    def __init__(self, *args, **kwargs):
        self.doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = DoctorLeave
        fields = ['leave_date', 'reason']
        widgets = {
            'leave_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'input input-bordered w-full rounded-xl text-sm focus:input-primary bg-white text-slate-900'
            }),
            'reason': forms.TextInput(attrs={
                'placeholder': 'e.g. Medical Conference / Personal Leave',
                'class': 'input input-bordered w-full rounded-xl text-sm focus:input-primary bg-white text-slate-900'
            }),
        }

    def clean_leave_date(self):
        leave_date = self.cleaned_data.get('leave_date')
        if leave_date:
            if leave_date < timezone.localdate():
                raise forms.ValidationError("Leave date cannot be in the past.")
            if self.doctor and DoctorLeave.objects.filter(doctor=self.doctor, leave_date=leave_date).exists():
                raise forms.ValidationError(f"Leave is already logged for {leave_date.strftime('%b %d, %Y')}.")
        return leave_date

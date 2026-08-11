from django import forms
from .models import Event, EventSeg, Registration

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'banner', 'description', 'primary_color', 'status', 'date']

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        exclude = ['event', 'status', 'submitted_at']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'segment': forms.CheckboxSelectMultiple,
        }
    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)
        if event is not None:
            self.fields['segment'].queryset = EventSeg.objects.filter(event=event)
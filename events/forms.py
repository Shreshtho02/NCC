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
            'segment': forms.CheckboxSelectMultiple(),
            'dob': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)

        if event is not None:
            self.fields['segment'].queryset = EventSeg.objects.filter(event=event)

        base_input_classes = (
            "bg-surface border border-text-muted/30 text-text rounded-lg "
            "px-3 py-2 w-full focus:outline-none focus:border-[var(--event-accent)] "
            "transition"
        )

        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxSelectMultiple):
                widget.attrs['class'] = 'accent-[var(--event-accent)]'
            else:
                widget.attrs['class'] = base_input_classes
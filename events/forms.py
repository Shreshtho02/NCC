from django import forms
from .models import Event, EventSeg, Participant, CampusAmbassador

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'banner', 'description', 'primary_color', 'status', 'date']

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Participant
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

class CampusAmbassadorForm(forms.ModelForm):
    class Meta:
        model = CampusAmbassador
        exclude = ['batch', 'status', 'submitted_at']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'motivation': forms.Textarea(attrs={'rows': 4}),
            'help_plan': forms.Textarea(attrs={'rows': 4}),
            'past_experience': forms.Textarea(attrs={'rows': 3}),
            'club_affiliation': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, batch=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch = batch

        if batch is not None and not batch.requires_reference:
            del self.fields['reference_code']

        base_input_classes = (
            "bg-surface border border-text-muted/30 text-text rounded-lg "
            "px-3 py-2 w-full focus:outline-none focus:border-[var(--event-accent)] "
            "transition"
        )
        for name, field in self.fields.items():
            field.widget.attrs['class'] = base_input_classes
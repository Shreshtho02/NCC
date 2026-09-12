from django import forms
import json

from .models import EventSeg, Participant


class RegistrationForm(forms.ModelForm):
    segment_selections = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Participant
        exclude = ['event', 'status', 'submitted_at', 'selected_subcategories']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)

        if event is not None:
            segments = list(EventSeg.objects.filter(event=event).order_by('name'))
            self.fields['segment'].queryset = EventSeg.objects.filter(pk__in=[s.pk for s in segments])
        else:
            segments = list(self.fields['segment'].queryset)

        selected_ids = set(self.data.getlist('segment')) if self.is_bound else {
            str(segment.pk) for segment in self.initial.get('segment', [])
        }

        self.segment_cards = []
        self.segment_option_data = {}
        for segment in segments:
            options = segment.get_subcategory_options()
            self.segment_cards.append({
                'segment': segment,
                'options': options,
                'selected': str(segment.pk) in selected_ids,
            })
            self.segment_option_data[str(segment.pk)] = {
                'name': segment.name,
                'options': options,
                'fee': segment.fee,
            }

        base_input_classes = (
            "bg-surface border border-text-muted/30 text-text rounded-lg "
            "px-3 py-2 w-full focus:outline-none focus:border-[var(--event-accent)] "
            "transition"
        )
        for name, field in self.fields.items():
            if name != 'segment':
                field.widget.attrs['class'] = base_input_classes

    def clean_segment_selections(self):
        raw_selections = self.cleaned_data['segment_selections']
        if not raw_selections:
            return {}
        try:
            selections = json.loads(raw_selections)
        except json.JSONDecodeError as error:
            raise forms.ValidationError('Invalid segment option selection.') from error
        if not isinstance(selections, dict) or not all(
            isinstance(segment_id, str) and isinstance(option, str)
            for segment_id, option in selections.items()
        ):
            raise forms.ValidationError('Invalid segment option selection.')
        return selections

    def clean(self):
        cleaned_data = super().clean()
        selected_segments = cleaned_data.get('segment')
        if not selected_segments:
            return cleaned_data

        selections = cleaned_data.get('segment_selections')
        if selections is None:
            # segment_selections already failed validation in clean_segment_selections —
            # don't pile a second, confusing error on top of that one.
            return cleaned_data

        selected_ids = {str(segment.pk) for segment in selected_segments}
        if not set(selections).issubset(selected_ids):
            self.add_error('segment', 'Choose options only for selected segments.')

        email = cleaned_data.get('email')
        for segment in selected_segments:
            options = segment.get_subcategory_options()
            if options and selections.get(str(segment.pk)) not in options:
                self.add_error('segment', f'Choose an option for {segment.name}.')
            if email and Participant.objects.filter(email=email, segment=segment).exclude(pk=self.instance.pk).exists():
                self.add_error('segment', f'You are already registered for {segment.name}.')

        return cleaned_data

    def save(self, commit=True):
        registration = super().save(commit=False)
        registration.selected_subcategories = self.cleaned_data.get('segment_selections', {})
        if commit:
            registration.save()
            self.save_m2m()
        return registration
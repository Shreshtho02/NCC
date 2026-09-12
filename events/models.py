import os
from django.db import models
from django.utils.text import slugify
from colorfield.fields import ColorField
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from urllib.parse import urlencode
from django.utils.text import Truncator

current_year = datetime.now().year

def banner_renamer(instance,file):
    extension = file.split('.')[-1]
    slug = instance.slug
    renamed_file = f"{slug}.{extension}"
    return os.path.join('banners', renamed_file)

def segment_icon_renamer(instance, file):
    # EventSeg has no slug of its own, so we build a stable name from the parent
    # event's slug + the segment name. Like banner_renamer, this depends on
    # instance.event and instance.name already being set before save() — pk
    # isn't assigned yet at this point for a brand-new segment, so it can't be used.
    extension = file.split('.')[-1]
    event_slug = instance.event.slug if instance.event_id else 'unassigned'
    segment_slug = slugify(instance.name) or 'segment'
    return os.path.join('segment_icons', f"{event_slug}-{segment_slug}.{extension}")

class Event(models.Model):
    STATUS = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('done', 'Done')
    ]
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    banner = models.ImageField(upload_to=banner_renamer)
    description = models.TextField()
    primary_color = ColorField(default="#FFFF00")
    status = models.CharField(max_length=10, choices=STATUS, default='upcoming')
    date = models.DateField()
    facebook_url = models.URLField(blank=True, help_text="Link to the event's Facebook page/post, if any.")

    def __str__(self):
        return self.name

    def get_eligibility_range(self):
        eligibilities = list(self.eligibilities.all())
        if not eligibilities:
            return None
        start_code = min(e.start for e in eligibilities)
        end_code = max(e.end for e in eligibilities)
        choices = dict(Eligibility.CLASS_CHOICES)
        return {'start': choices[start_code], 'end': choices[end_code]}

    def google_calendar_url(self):
        start = self.date.strftime('%Y%m%d')
        end = (self.date + timedelta(days=1)).strftime('%Y%m%d')
        summary = Truncator(self.description).chars(150)
        params = {
            'action': 'TEMPLATE',
            'text': self.name,
            'dates': f'{start}/{end}',
            'details': summary,
        }
        return f'https://calendar.google.com/calendar/render?{urlencode(params)}'

class Eligibility(models.Model):
    CLASS_CHOICES = [
        ('c01', 'Class 1'),
        ('c02', 'Class 2'),
        ('c03', 'Class 3'),
        ('c04', 'Class 4'),
        ('c05', 'Class 5'),
        ('c06', 'Class 6'),
        ('c07', 'Class 7'),
        ('c08', 'Class 8'),
        ('c09', 'Class 9'),
        ('c10', 'Class 10'),
        ('c11', 'Class 11'),
        ('c12', 'Class 12'),
        ('c13', f'HSC {current_year}')
    ]
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='eligibilities')
    name = models.CharField(max_length=100)
    start = models.CharField(max_length=4, choices=CLASS_CHOICES)
    end = models.CharField(max_length=4, choices=CLASS_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.get_start_display()} to {self.get_end_display()})"

    def clean(self):
        if self.start > self.end:
            raise ValidationError({
                'start': "The starting class cannot be higher than the ending class."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class EventSeg(models.Model):
    FORMAT_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
    ]
    ICON_CHOICES = [
        ('music', 'Music / Singing'),
        ('dance', 'Dance'),
        ('drama', 'Drama / Acting'),
        ('art', 'Art / Design'),
        ('photography', 'Photography'),
        ('writing', 'Writing'),
        ('quiz', 'Quiz / Trivia'),
        ('speech', 'Speech / Debate'),
        ('comedy', 'Comedy'),
        ('film', 'Film / Video'),
        ('tech', 'Tech / Gaming'),
        ('general', 'General'),
    ]
    name = models.CharField(max_length=100)
    group_label = models.CharField(
        max_length=100, blank=True,
        help_text="Optional heading to cluster related segments on the event page, e.g. 'Singing', 'Quiz Arena'."
    )
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    icon = models.CharField(
        max_length=20, choices=ICON_CHOICES, default='general',
        help_text="Fallback icon shown if no custom icon image (below) is uploaded."
    )
    icon_image = models.ImageField(
        upload_to=segment_icon_renamer, blank=True, null=True,
        help_text="Optional custom icon/logo for this specific segment. Overrides the fallback icon above when set."
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='segmentset')
    fee = models.PositiveIntegerField()
    eligibility = models.ForeignKey(Eligibility, on_delete=models.PROTECT, related_name='segments')
    is_group = models.BooleanField(default=False)
    team_size = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Members per team — only meaningful if is_group is True."
    )
    subcategories = models.CharField(
        max_length=300, blank=True,
        help_text="Comma-separated styles/options, display only, e.g. 'Patriotic, Folk, Modern/Band'."
    )

    def get_subcategory_options(self):
        return [option.strip() for option in self.subcategories.split(',') if option.strip()]

    def __str__(self):
        return self.name

# Campus Ambassador models were removed in migration 0011.
class Participant(models.Model):
    STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    PAYMENT_METHODS = [
        ('bkash', 'Bkash'),
        ('nagad', 'Nagad'),
        ('upay', 'Upay')
    ]
    PARTICIPANT_CLASS = Eligibility.CLASS_CHOICES + [
        ('university', 'University Student'),
        ('na', 'Not a Student')
    ]
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    segment = models.ManyToManyField(EventSeg)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    phone = models.CharField(max_length=20)
    dob = models.DateField(blank=True, null=True)
    institution = models.CharField(max_length=200, blank=True)
    caref = models.CharField(max_length=100, blank=True)
    trxid = models.CharField(max_length=100, unique=True)
    paymeth = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    paynum = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=STATUS, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    addnote = models.TextField(blank=True)
    participant_class = models.CharField(max_length=15, choices=PARTICIPANT_CLASS, blank=True, null=True)
    selected_subcategories = models.JSONField(default=dict, blank=True)

    def clean(self):
        # Only meaningful on updates (e.g. admin editing an existing registration) —
        # the M2M can't be queried before the instance has a pk. The real
        # duplicate-registration check for new submissions lives in
        # RegistrationForm.clean(), where selected segments are already
        # available pre-save.
        if self.pk:
            for seg in self.segment.all():
                if seg.event_id != self.event_id:
                    raise ValidationError(f"{seg.name} does not belong to {self.event.name}.")

    def __str__(self):
        return self.name
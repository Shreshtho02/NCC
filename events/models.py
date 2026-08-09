from django.db import models
# from django.utils.text import slugify
from colorfield.fields import ColorField
from django.core.exceptions import ValidationError
from datetime import datetime
current_year = datetime.now().year

# Create your models here.
class Event(models.Model):
    STATUS = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('done', 'Done')
    ]
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    banner = models.ImageField(upload_to='banners')
    description = models.TextField()
    primary_color = ColorField(default="#FFFF00")
    status = models.CharField(max_length=10, choices=STATUS, default='upcoming')
    date = models.DateField()

    def __str__(self):
        return self.name


class EventSeg(models.Model):
    CATEGORIES = [
        ('all', 'For everyone'),
        ('students', 'For School and College Students'),
        ('custom', 'Create Custom Category')
    ]
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    fee = models.PositiveIntegerField()
    category = models.CharField(max_length=20, choices=CATEGORIES, default='students')

    def __str__(self):
        return self.name

class ClassRange(models.Model):
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
        ('c13', 'This year HSC Batch')
    ]
    name = models.CharField(max_length=100)
    start = models.CharField(max_length=4, choices=CLASS_CHOICES)
    end = models.CharField(max_length=4, choices=CLASS_CHOICES)
    segment = models.ForeignKey(EventSeg, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.get_start_display()} to {self.get_end_display()})"

    def clean(self):
        if self.start > self.end:
            raise ValidationError({
                'start': "The starting class cannot be higher than the ending class."
            })
        if self.segment.category != 'custom':
            raise ValidationError({
                'start': "The class range choices will show only when the 'custom' category is selected."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class Registration(models.Model):
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
    PARTICIPANT_CLASS = ClassRange.CLASS_CHOICES + [
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

    def clean(self):
        if self.pk:
            selected_segments = self.segment.all()
            for seg in selected_segments:
                if seg.event_id != self.event_id:
                    raise ValidationError(f"{seg.name} does not belong to {self.event.name}.")
                already_registered = Registration.objects.filter(
                    email=self.email,
                    segment=seg
                ).exclude(pk=self.pk).exists()
                if already_registered:
                    raise ValidationError(f"{self.email} is already registered for {seg.name}.")

    def __str__(self):
        return self.name
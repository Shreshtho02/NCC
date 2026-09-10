import os
from django.db import models
# from django.utils.text import slugify
from colorfield.fields import ColorField
from django.core.exceptions import ValidationError
from datetime import datetime
current_year = datetime.now().year

def banner_renamer(instance,file):
    extension = file.split('.')[-1]
    slug = instance.slug
    renamed_file = f"{slug}.{extension}"
    return os.path.join('banners', renamed_file)

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

    def __str__(self):
        return self.name
    

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
        ('c13', 'This year HSC Batch')
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
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='segmentset')
    fee = models.PositiveIntegerField()
    eligibility = models.ForeignKey(Eligibility, on_delete=models.PROTECT, related_name='segments', null=True, blank=True)

    def __str__(self):
        return self.name


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

    def clean(self):
        if self.pk:
            selected_segments = self.segment.all()
            for seg in selected_segments:
                if seg.event_id != self.event_id:
                    raise ValidationError(f"{seg.name} does not belong to {self.event.name}.")
                already_registered = Participant.objects.filter(
                    email=self.email,
                    segment=seg
                ).exclude(pk=self.pk).exists()
                if already_registered:
                    raise ValidationError(f"{self.email} is already registered for {seg.name}.")

    def __str__(self):
        return self.name


class CABatch(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ca_batches')
    name = models.CharField(max_length=100)
    is_open = models.BooleanField(default=False)
    requires_reference = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.event.name} — {self.name}"

    def clean(self):
        if self.is_open:
            conflict = CABatch.objects.filter(
                event=self.event,
                is_open=True
            ).exclude(pk=self.pk).exists()
            if conflict:
                raise ValidationError(
                    "Another batch for this event is already open. Close it before opening this one."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class CampusAmbassador(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    PARTICIPANTS_ESTIMATE = [
        ('10', '10'),
        ('20', '20'),
        ('30', '30'),
        ('40', '40'),
        ('40+', '40+'),
    ]
    STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    batch = models.ForeignKey(CABatch, on_delete=models.CASCADE, related_name='applicants')
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    email = models.EmailField(max_length=100)
    institution = models.CharField(max_length=200)
    class_batch = models.CharField(max_length=4, choices=Eligibility.CLASS_CHOICES)
    address = models.TextField()
    facebook = models.URLField()
    instagram = models.URLField(blank=True)
    past_experience = models.TextField(blank=True)
    club_affiliation = models.TextField(blank=True)
    motivation = models.TextField()
    participants_estimate = models.CharField(max_length=3, choices=PARTICIPANTS_ESTIMATE)
    help_plan = models.TextField()
    photo = models.ImageField(upload_to='ca_photos/')
    reference_code = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name
from django.contrib import admin
from .models import *
# Register your models here.

class EligibilityInline(admin.TabularInline):
    model = Eligibility
    extra = 1

class EventAdmin(admin.ModelAdmin):
    inlines = [EligibilityInline]

admin.site.register(Event, EventAdmin)
admin.site.register(EventSeg)
admin.site.register(Eligibility)
admin.site.register(Participant)

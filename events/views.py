from django.shortcuts import render, redirect, get_object_or_404
from .forms import EventForm, RegistrationForm
from .models import *

# Create your views here.
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('event_list')
    else:
        form = EventForm()

    return render(request, 'events/event_form.html', {'form': form})

def event_detail(request, slug):
    event = get_object_or_404(Event, slug=slug)
    segments = event.segmentset.all()
    context = {
        'event': event,
        'segments': segments
    }
    return render(request, 'events/event_detail.html', context)

def event_register(request, slug):
    event = get_object_or_404(Event, slug=slug)
    if request.method == 'POST':
        form = RegistrationForm(request.POST, event=event)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.event = event
            registration.save()
            form.save_m2m()
            return redirect('event_detail', slug=event.slug)
    else: form = RegistrationForm(event=event)

    context = {'event': event, 'form':form}

    return render(request, 'events/event_register.html', context)

def event_list(request):
    events = Event.objects.all()
    return render(request, 'events/event_list.html', {'events':events})
from django.shortcuts import render, redirect, get_object_or_404
from .forms import EventForm
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
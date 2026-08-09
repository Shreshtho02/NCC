from django.shortcuts import render, redirect
from .forms import EventForm

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


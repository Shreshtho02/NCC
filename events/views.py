from django.shortcuts import render, redirect, get_object_or_404
from .forms import EventForm, RegistrationForm, CampusAmbassadorForm
from .models import *
from django.http import Http404, HttpResponse
from .receipts import build_receipt_image
from django.core import signing
from django.core.signing import BadSignature

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
            token = signing.dumps(registration.pk)
            return redirect('registration_success', slug=event.slug, token=token)
    else:
        form = RegistrationForm(event=event)

    context = {'event': event, 'form': form}
    return render(request, 'events/event_register.html', context)

def _get_registration_from_token(token):
    try:
        pk = signing.loads(token, max_age=60 * 60 * 24)  # token valid 24h
    except BadSignature:
        raise Http404
    return get_object_or_404(Participant, pk=pk)

def event_list(request):
    events = Event.objects.all()
    return render(request, 'events/event_list.html', {'events':events})


def registration_success(request, slug, token):
    registration = _get_registration_from_token(token)
    total_fee = sum(seg.fee for seg in registration.segment.all())
    context = {
        'event': registration.event,
        'registration': registration,
        'segments': registration.segment.all(),
        'total_fee': total_fee,
        'token': token,
    }
    return render(request, 'events/registration_success.html', context)

def registration_receipt(request, token):
    registration = _get_registration_from_token(token)
    buffer = build_receipt_image(registration)
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="receipt-{registration.trxid}.png"'
    return response


def ca_register(request, slug):
    event = get_object_or_404(Event, slug=slug)
    batch = event.ca_batches.filter(is_open=True).first()

    if batch is None:
        return render(request, 'events/ca_closed.html', {'event': event})

    if request.method == 'POST':
        form = CampusAmbassadorForm(request.POST, request.FILES, batch=batch)
        if form.is_valid():
            applicant = form.save(commit=False)
            applicant.batch = batch
            applicant.save()
            return redirect('event_detail', slug=event.slug)
    else:
        form = CampusAmbassadorForm(batch=batch)

    context = {'event': event, 'batch': batch, 'form': form}
    return render(request, 'events/ca_register.html', context)
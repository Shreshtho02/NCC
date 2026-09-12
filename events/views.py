from itertools import groupby

from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm
from .models import *
from django.http import Http404, HttpResponse
from .receipts import build_receipt_image
from django.core import signing
from django.core.signing import BadSignature


def event_detail(request, slug):
    event = get_object_or_404(Event, slug=slug)
    segments = event.segmentset.order_by('group_label', 'id')

    offline_segments = [s for s in segments if not s.is_group and s.format == 'offline']
    online_segments = [s for s in segments if not s.is_group and s.format == 'online']

    team_segments = [s for s in segments if s.is_group]
    offline_team_groups = [
        {'label': label or 'Team Segments', 'segments': list(group)}
        for label, group in groupby(
            (s for s in team_segments if s.format == 'offline'), key=lambda s: s.group_label,
        )
    ]
    online_team_groups = [
        {'label': label or 'Team Segments', 'segments': list(group)}
        for label, group in groupby(
            (s for s in team_segments if s.format == 'online'), key=lambda s: s.group_label,
        )
    ]

    context = {
        'event': event,
        'offline_segments': offline_segments,
        'offline_team_groups': offline_team_groups,
        'online_segments': online_segments,
        'online_team_groups': online_team_groups,
        'sponsor_placeholders': [f'Sponsor {i}' for i in range(1, 7)],
        'partner_placeholders': [f'Partner {i}' for i in range(1, 5)],
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
    return render(request, 'events/event_list.html', {'events': events})


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
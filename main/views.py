from django.shortcuts import render
from events.models import Event

from django.shortcuts import render
from events.models import Event

def home(request):
    context = {
        'title': 'Home',
        'flagship': Event.objects.filter(slug='ncc').first(),
        'other_events': Event.objects.exclude(slug='ncc')[:6],
        'departments': [
            {'name': 'Wordspace', 'blurb': 'Writing, editorial, and content for the club.'},
            {'name': 'Art & Craft Station', 'blurb': 'Visual design, illustration, installations.'},
            {'name': 'IT and Logistics', 'blurb': 'The site, the systems, the setup on the day.'},
            {'name': 'Verbal Artistry', 'blurb': 'Debate, recitation, extempore.'},
            {'name': 'Music', 'blurb': 'Vocals, instruments, sound.'},
            {'name': 'Public Relations', 'blurb': 'Sponsors, press, outward-facing everything.'},
            {'name': 'Gesture Artistry', 'blurb': 'Dance, drama, stage movement.'},
        ],
        'gallery': [
            {'src': '/media/gallery/1.jpg', 'alt': 'Rehearsal backstage'},
            {'src': '/media/gallery/2.jpg', 'alt': 'Opening night crowd'},
            {'src': '/media/gallery/3.jpg', 'alt': 'Award ceremony'},
        ],
        'moderators': [
            {'name': 'Full Name', 'role': 'Chief Moderator', 'photo': '/media/committee/placeholder.jpg'},
            {'name': 'Full Name', 'role': 'Moderator', 'photo': '/media/committee/placeholder.jpg'},
        ],
        'panelists': [
            {'name': 'Full Name', 'role': 'Panelist', 'photo': '/media/committee/placeholder.jpg'},
            {'name': 'Full Name', 'role': 'Panelist', 'photo': '/media/committee/placeholder.jpg'},
            {'name': 'Full Name', 'role': 'Panelist', 'photo': '/media/committee/placeholder.jpg'},
            {'name': 'Full Name', 'role': 'Panelist', 'photo': '/media/committee/placeholder.jpg'},
            {'name': 'Full Name', 'role': 'Panelist', 'photo': '/media/committee/placeholder.jpg'},
        ],
    }
    return render(request, 'main/index.html', context)

def about(request):
    context = {'title': 'About'}
    return render(request, 'main/about.html', context)
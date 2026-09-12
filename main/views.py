from django.shortcuts import render
from events.models import Event

def home(request):
    context = {
        'title': 'Home',
        'flagship': Event.objects.filter(slug='ncc').first(),
    }
    return render(request, 'main/index.html', context)

def about(request):
    context = {'title': 'About'}
    return render(request, 'main/about.html', context)
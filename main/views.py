from django.shortcuts import render

# Create your views here.
def home(request):
    context = {
        'title': 'Home'
    }

    return render(request, 'main/index.html', context)

def about(request):
    context = {
        'title': 'About'
    }

    return render(request, 'main/about.html', context)
from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_event, name='create_event'),
    path('<slug:slug>/', views.event_detail, name='event_detail')
]
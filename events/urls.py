from django.urls import path
from . import views

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('create/', views.create_event, name='create_event'),
    path('<slug:slug>/', views.event_detail, name='event_detail'),
    path('<slug:slug>/register/', views.event_register, name='event_register')
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('<slug:slug>/', views.event_detail, name='event_detail'),
    path('<slug:slug>/register/', views.event_register, name='event_register'),
    path('<slug:slug>/register/success/<str:token>/', views.registration_success, name='registration_success'),
    path('registration/<str:token>/receipt/', views.registration_receipt, name='registration_receipt'),
]

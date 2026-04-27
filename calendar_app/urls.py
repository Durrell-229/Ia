from django.urls import path
from . import views

app_name = 'calendar_app'

urlpatterns = [
    path('', views.calendar_view, name='calendar'),
    path('api/events/', views.event_list_api, name='event_list_api'),
    path('api/events/create/', views.event_create_api, name='event_create_api'),
]

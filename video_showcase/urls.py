from django.urls import path
from . import views

app_name = 'video_showcase'

urlpatterns = [
    path('', views.showcase_view, name='showcase'),
]

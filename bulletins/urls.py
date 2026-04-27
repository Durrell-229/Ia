from django.urls import path
from . import views

app_name = 'bulletins'

urlpatterns = [
    path('', views.index, name='index'),
    path('<uuid:bulletin_id>/', views.detail, name='detail'),
]

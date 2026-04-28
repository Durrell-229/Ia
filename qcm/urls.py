from django.urls import path
from . import views

urlpatterns = [
    path('start/', views.qcm_start_view, name='qcm_start'),
    path('submit/', views.qcm_submit_view, name='qcm_submit'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('start/', views.start_qcm, name='qcm_start'),
    path('submit/', views.submit_qcm, name='qcm_submit'),
]

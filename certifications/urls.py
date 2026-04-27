from django.urls import path
from . import views

urlpatterns = [
    path('verify/<str:code>/', views.verify_certificate_view, name='verify_certificate'),
    path('api/verify/', views.verify_certificate_api, name='verify_certificate_api'),
    path('my/', views.my_certificates_view, name='my_certificates'),
]

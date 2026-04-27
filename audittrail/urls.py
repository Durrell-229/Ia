from django.urls import path
from . import views

urlpatterns = [
    path('logs/', views.audit_log_view, name='audit_logs'),
    path('logs/list/', views.audit_log_view, name='audit_list'),
    path('export/', views.export_data_view, name='export_data'),
]

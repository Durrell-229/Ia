from django.urls import path
from . import views

urlpatterns = [
    path('check/<str:exam_id>/', views.run_plagiarism_check_view, name='run_plagiarism_check'),
    path('report/<str:check_id>/', views.plagiarism_report_view, name='plagiarism_report'),
]

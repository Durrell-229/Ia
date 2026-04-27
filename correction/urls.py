from django.urls import path
from . import views

urlpatterns = [
    path('upload/<uuid:exam_id>/', views.upload_submission, name='upload_submission'),
    path('approve/<uuid:submission_id>/', views.approve_submission, name='approve_submission'),
    path('download-bulletin/<uuid:submission_id>/', views.download_bulletin, name='download_bulletin'),
]

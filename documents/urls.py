from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.document_list, name='document_list'),
    path('upload/', views.document_upload, name='document_upload'),
    path('<str:doc_id>/', views.document_detail, name='document_detail'),
    path('<str:doc_id>/download/', views.document_download, name='document_download'),
]

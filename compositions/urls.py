from django.urls import path
from . import views

urlpatterns = [
    path('room/<str:exam_id>/', views.composition_room_view, name='composition_room'),
    path('submit-paper/<str:session_id>/', views.submit_paper_view, name='submit_paper'),
    path('result/<str:session_id>/', views.result_view, name='result_detail'),
    path('ia-corrections/', views.ia_corrections_list_view, name='ia_corrections_list'),
]

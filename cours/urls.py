from django.urls import path
from . import views

urlpatterns = [
    path('', views.course_list_view, name='index'), 
    path('create/', views.create_course, name='create_course'),
    path('<uuid:course_id>/', views.course_detail, name='detail'),
    path('qcm/create/<uuid:course_id>/', views.create_qcm_view, name='create_qcm'),
    path('admin/approve/<uuid:course_id>/', views.admin_approve_course, name='admin_approve_course'),
]

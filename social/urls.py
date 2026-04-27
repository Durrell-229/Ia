from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    path('', views.forum_list, name='forum_list'),
    path('forum/<str:forum_id>/', views.forum_detail, name='forum_detail'),
    path('topic/<str:topic_id>/', views.topic_detail, name='topic_detail'),
    path('groups/', views.group_list, name='group_list'),
    path('groups/create/', views.group_create, name='group_create'),
    path('groups/<str:group_id>/', views.group_detail, name='group_detail'),
]

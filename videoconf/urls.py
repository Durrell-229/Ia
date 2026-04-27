from django.urls import path
from . import views

app_name = 'videoconf'

urlpatterns = [
    path('', views.rooms_list_view, name='rooms_list'),
    path('create/', views.create_room_view, name='create_room'),
    path('room/<str:room_id>/', views.room_detail_view, name='room_detail'),
    path('room/<str:room_id>/join/', views.join_room_view, name='join_room'),
    path('room/<str:room_id>/leave/', views.leave_room_view, name='leave_room'),
]

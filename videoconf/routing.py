from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/room/<str:room_id>/', consumers.RoomConsumer.as_asgi(), name='room_ws'),
    path('ws/rooms/', consumers.RoomListConsumer.as_asgi(), name='room_list_ws'),
]

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

from .models import MeetingRoom, RoomParticipant, RoomMessage


class RoomConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for a specific meeting room."""

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'room_{self.room_id}'
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Send current participants
        participants = await self._get_participants()
        await self.send(text_data=json.dumps({
            'type': 'participants_list',
            'participants': participants,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'chat_message':
            await self._handle_chat_message(data)
        elif action == 'participant_joined':
            await self._broadcast_participant_joined(data)
        elif action == 'participant_left':
            await self._broadcast_participant_left(data)
        elif action == 'toggle_mute':
            await self._handle_toggle_mute(data)
        elif action == 'toggle_camera':
            await self._handle_toggle_camera(data)

    async def chat_message(self, event):
        """Broadcast chat message to room."""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
        }))

    async def participant_update(self, event):
        """Broadcast participant update to room."""
        await self.send(text_data=json.dumps({
            'type': 'participant_update',
            'update': event['update'],
        }))

    async def room_state_update(self, event):
        """Broadcast room state update."""
        await self.send(text_data=json.dumps({
            'type': 'room_state',
            'state': event['state'],
        }))

    @database_sync_to_async
    def _handle_chat_message(self, data):
        """Save and broadcast chat message."""
        content = data.get('content', '').strip()
        if not content:
            return

        msg = RoomMessage.objects.create(
            room_id=self.room_id,
            user=self.user,
            content=content,
        )

        message_data = {
            'id': str(msg.id),
            'user_id': str(msg.user.id),
            'user_name': msg.user.full_name,
            'user_avatar': msg.user.avatar.url if msg.user.avatar else None,
            'content': msg.content,
            'created_at': msg.created_at.isoformat(),
            'is_system_message': msg.is_system_message,
        }

        # Broadcast to room
        self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_data,
            }
        )

    @database_sync_to_async
    def _broadcast_participant_joined(self, data):
        """Broadcast that a participant joined."""
        rp, _ = RoomParticipant.objects.get_or_create(
            room_id=self.room_id,
            user=self.user,
            defaults={'role': 'participant'}
        )

        update = {
            'action': 'joined',
            'user_id': str(self.user.id),
            'user_name': self.user.full_name,
            'user_avatar': self.user.avatar.url if self.user.avatar else None,
            'role': rp.role,
        }

        self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'participant_update',
                'update': update,
            }
        )

    @database_sync_to_async
    def _broadcast_participant_left(self, data):
        """Broadcast that a participant left."""
        try:
            rp = RoomParticipant.objects.get(
                room_id=self.room_id, user=self.user
            )
            rp.status = 'left'
            rp.left_at = timezone.now()
            rp.save()
        except RoomParticipant.DoesNotExist:
            pass

        update = {
            'action': 'left',
            'user_id': str(self.user.id),
            'user_name': self.user.full_name,
        }

        self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'participant_update',
                'update': update,
            }
        )

    @database_sync_to_async
    def _handle_toggle_mute(self, data):
        """Toggle mute state."""
        try:
            rp = RoomParticipant.objects.get(
                room_id=self.room_id, user=self.user
            )
            rp.is_muted = not rp.is_muted
            rp.save()

            update = {
                'action': 'muted',
                'user_id': str(self.user.id),
                'is_muted': rp.is_muted,
            }

            self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'participant_update',
                    'update': update,
                }
            )
        except RoomParticipant.DoesNotExist:
            pass

    @database_sync_to_async
    def _handle_toggle_camera(self, data):
        """Toggle camera state."""
        try:
            rp = RoomParticipant.objects.get(
                room_id=self.room_id, user=self.user
            )
            rp.is_camera_on = not rp.is_camera_on
            rp.save()

            update = {
                'action': 'camera',
                'user_id': str(self.user.id),
                'is_camera_on': rp.is_camera_on,
            }

            self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'participant_update',
                    'update': update,
                }
            )
        except RoomParticipant.DoesNotExist:
            pass

    @database_sync_to_async
    def _get_participants(self):
        """Get current participants in the room."""
        participants = RoomParticipant.objects.filter(
            room_id=self.room_id, status='in_room'
        ).select_related('user')

        return [
            {
                'user_id': str(p.user.id),
                'user_name': p.user.full_name,
                'user_avatar': p.user.avatar.url if p.user.avatar else None,
                'role': p.role,
                'is_muted': p.is_muted,
                'is_camera_on': p.is_camera_on,
            }
            for p in participants
        ]


class RoomListConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for room list updates."""

    async def connect(self):
        self.group_name = 'room_list'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        # Send initial room list
        rooms = await self._get_active_rooms()
        await self.send(text_data=json.dumps({
            'type': 'room_list',
            'rooms': rooms,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def room_created(self, event):
        """Broadcast new room."""
        await self.send(text_data=json.dumps({
            'type': 'room_created',
            'room': event['room'],
        }))

    async def room_ended(self, event):
        """Broadcast room ended."""
        await self.send(text_data=json.dumps({
            'type': 'room_ended',
            'room_id': event['room_id'],
        }))

    async def room_status_change(self, event):
        """Broadcast room status change."""
        await self.send(text_data=json.dumps({
            'type': 'room_status_change',
            'room': event['room'],
        }))

    @database_sync_to_async
    def _get_active_rooms(self):
        """Get active rooms."""
        rooms = MeetingRoom.objects.filter(
            is_active=True
        ).exclude(status=MeetingRoom.Status.ENDED).order_by('-created_at')

        return [
            {
                'id': str(r.id),
                'name': r.name,
                'status': r.status,
                'is_public': r.is_public,
                'participant_count': r.participant_count,
                'max_participants': r.max_participants,
                'created_by_name': r.created_by.full_name,
                'has_google_meet': bool(r.google_meet_link),
                'created_at': r.created_at.isoformat(),
            }
            for r in rooms
        ]

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return

        self.group_name = f"user_{self.user.id}_notifications"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({"type": "connected", "message": "Connexion temps réel établie."}))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        if action == 'mark_read':
            notification_id = data.get('notification_id')
            await self.mark_notification_read(notification_id)
            await self.send(text_data=json.dumps({"type": "marked_read", "id": notification_id}))

    async def notification_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "notification",
            "id": event.get("id"),
            "title": event.get("title"),
            "message": event.get("message"),
            "notification_type": event.get("notification_type"),
            "link": event.get("link"),
            "created_at": event.get("created_at"),
        }))

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        from .models import Notification
        try:
            notif = Notification.objects.get(id=notification_id, destinataire=self.user)
            notif.is_read = True
            notif.save()
        except Notification.DoesNotExist:
            pass

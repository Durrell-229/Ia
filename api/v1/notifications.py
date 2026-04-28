from django.db import models
from ninja import Router, Schema
from notifications.models import Notification
from django.utils import timezone
from typing import List, Optional
import uuid

router = Router()

class NotificationOut(Schema):
    id: uuid.UUID
    titre: str
    message: str
    type_alerte: str
    created_at: timezone.datetime
    is_read: bool

@router.get("/", response=List[NotificationOut])
def list_notifications(request):
    """Liste les notifications de l'utilisateur (globales + privées)"""
    if not request.user.is_authenticated:
        return []
        
    return Notification.objects.filter(
        models.Q(recipient=request.user) | models.Q(recipient__isnull=True)
    ).order_by('-created_at')[:20]

@router.post("/{notification_id}/read")
def mark_as_read(request, notification_id: uuid.UUID):
    """Marque une notification comme lue"""
    if not request.user.is_authenticated:
        return {"success": False}
        
    Notification.objects.filter(id=notification_id, recipient=request.user).update(is_read=True)
    return {"success": True}

@router.get("/unread-count")
def unread_count(request):
    """Nombre de notifications non lues"""
    if not request.user.is_authenticated:
        return {"count": 0}
        
    count = Notification.objects.filter(
        models.Q(recipient=request.user) | models.Q(recipient__isnull=True),
        is_read=False
    ).count()
    return {"count": count}

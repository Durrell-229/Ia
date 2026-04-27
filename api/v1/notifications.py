from django.db import models
from ninja import Router, Schema
from notifications.models import GlobalAnnouncement
from django.utils import timezone
from typing import Optional, List
import uuid

router = Router()

class AnnouncementOut(Schema):
    id: uuid.UUID
    titre: str
    message: str
    type_alerte: str

@router.get("/latest-announcement", response=Optional[AnnouncementOut])
def get_latest_announcement(request):
    """
    Récupère la notification globale active.
    """
    now = timezone.now()
    announcement = GlobalAnnouncement.objects.filter(
        est_actif=True
    ).filter(
        models.Q(date_expiration__gt=now) | models.Q(date_expiration__isnull=True)
    ).first()
    
    return announcement

@router.get("/all", response=List[AnnouncementOut])
def list_announcements(request):
    return GlobalAnnouncement.objects.filter(est_actif=True)[:10]

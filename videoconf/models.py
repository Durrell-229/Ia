import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class MeetingRoom(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Planifiée'
        LIVE = 'live', 'En direct'
        ENDED = 'ended', 'Terminée'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Nom de la salle', max_length=255)
    description = models.TextField('Description', blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='created_rooms', verbose_name='Créateur'
    )
    google_meet_link = models.CharField('Lien Google Meet', max_length=500, blank=True)
    access_code = models.CharField("Code d'accès", max_length=20, blank=True)
    is_active = models.BooleanField('Active', default=True)
    is_public = models.BooleanField('Publique', default=True)
    max_participants = models.IntegerField('Participants max', default=50)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField('Débutée le', null=True, blank=True)
    ended_at = models.DateTimeField('Terminée le', null=True, blank=True)
    status = models.CharField(
        'Statut', max_length=20, choices=Status.choices, default=Status.SCHEDULED
    )

    class Meta:
        verbose_name = 'Salle de réunion'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    @property
    def participant_count(self):
        return self.participants.filter(status='in_room').count()

    @property
    def is_live(self):
        return self.status == self.Status.LIVE


class RoomParticipant(models.Model):
    class Role(models.TextChoices):
        HOST = 'host', 'Hôte'
        MODERATOR = 'moderator', 'Modérateur'
        PARTICIPANT = 'participant', 'Participant'

    class Status(models.TextChoices):
        IN_WAITING_ROOM = 'waiting', 'Salle d\'attente'
        IN_ROOM = 'in_room', 'Dans la salle'
        LEFT = 'left', 'A quitté'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(
        MeetingRoom, on_delete=models.CASCADE,
        related_name='participants', verbose_name='Salle'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='room_participations', verbose_name='Utilisateur'
    )
    role = models.CharField(
        'Rôle', max_length=20, choices=Role.choices, default=Role.PARTICIPANT
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField('A quitté le', null=True, blank=True)
    is_muted = models.BooleanField('Muet', default=False)
    is_camera_on = models.BooleanField('Caméra active', default=True)
    status = models.CharField(
        'Statut', max_length=20, choices=Status.choices, default=Status.IN_ROOM
    )

    class Meta:
        verbose_name = 'Participant'
        unique_together = ['room', 'user']
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.full_name} dans {self.room.name}"


class RoomMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(
        MeetingRoom, on_delete=models.CASCADE,
        related_name='messages', verbose_name='Salle'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='room_messages', verbose_name='Utilisateur'
    )
    content = models.TextField('Message')
    created_at = models.DateTimeField(auto_now_add=True)
    is_system_message = models.BooleanField('Message système', default=False)

    class Meta:
        verbose_name = 'Message de salle'
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.room.name}] {self.user.full_name}: {self.content[:50]}"

import uuid
from django.db import models
from django.conf import settings


class CalendarEvent(models.Model):
    class EventType(models.TextChoices):
        EXAM = 'exam', 'Examen'
        CLASS = 'class', 'Cours'
        DEADLINE = 'deadline', 'Date limite'
        MEETING = 'meeting', 'Réunion'
        HOLIDAY = 'holiday', 'Vacances'
        OTHER = 'other', 'Autre'

    class EventColor(models.TextChoices):
        PRIMARY = 'primary', 'Bleu'
        SUCCESS = 'success', 'Vert'
        WARNING = 'warning', 'Orange'
        DANGER = 'danger', 'Rouge'
        INFO = 'info', 'Cyan'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField('Titre', max_length=255)
    description = models.TextField('Description', blank=True)
    event_type = models.CharField('Type', max_length=20, choices=EventType.choices, default=EventType.OTHER)
    color = models.CharField('Couleur', max_length=20, choices=EventColor.choices, default=EventColor.PRIMARY)
    start_date = models.DateTimeField('Date de début')
    end_date = models.DateTimeField('Date de fin', null=True, blank=True)
    is_all_day = models.BooleanField('Journée entière', default=False)
    location = models.CharField('Lieu', max_length=255, blank=True)
    link = models.URLField('Lien', blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='events')
    is_public = models.BooleanField('Public', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Événement'
        ordering = ['start_date']

    def __str__(self):
        return f"{self.title} ({self.start_date.strftime('%d/%m/%Y')})"


class EventReminder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(CalendarEvent, on_delete=models.CASCADE, related_name='reminders')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reminders')
    reminded_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Rappel'
        ordering = ['-reminded_at']

    def __str__(self):
        return f"Reminder for {self.event.title}"


class Attendance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(CalendarEvent, on_delete=models.CASCADE, related_name='attendances')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_present = models.BooleanField('Présent', default=False)
    checked_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['event', 'user']
        verbose_name = 'Présence'

    def __str__(self):
        return f"{self.user.full_name} - {self.event.title}"

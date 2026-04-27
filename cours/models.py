import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core.models import Matiere, Classe

class Course(models.Model):
    class Difficulty(models.TextChoices):
        BEGINNER = 'debutant', _('Débutant')
        INTERMEDIATE = 'intermediaire', _('Intermédiaire')
        ADVANCED = 'avance', _('Avancé')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('titre'), max_length=300)
    description = models.TextField(_('description'), blank=True)
    matiere = models.ForeignKey(Matiere, on_delete=models.SET_NULL, null=True, related_name='courses')
    classe = models.ForeignKey(Classe, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses_created', null=True, blank=True)
    thumbnail = models.ImageField(_('vignette'), upload_to='courses/thumbnails/', blank=True, null=True)
    difficulty = models.CharField(_('difficulté'), max_length=20, choices=Difficulty.choices, default=Difficulty.BEGINNER)
    estimated_time = models.CharField(_('temps estimé'), max_length=50, blank=True)
    is_published = models.BooleanField(default=False)
    status = models.CharField(_('statut approbation'), max_length=20, choices=[('pending', 'En attente'), ('approved', 'Approuvé'), ('rejected', 'Rejeté')], default='pending')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses_approved')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('cours')
        verbose_name_plural = _('cours')
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class CourseResource(models.Model):
    class ResourceType(models.TextChoices):
        VIDEO = 'video', _('Vidéo')
        AUDIO = 'audio', _('Audio / MP3')
        DOCUMENT = 'document', _('Document (PDF, Docx, etc.)')
        IMAGE = 'image', _('Image / Schéma')
        LINK = 'link', _('Lien Externe')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(_('titre de la ressource'), max_length=255)
    file_type = models.CharField(_('type'), max_length=20, choices=ResourceType.choices)
    file = models.FileField(_('fichier'), upload_to='courses/resources/%Y/%m/', blank=True, null=True)
    url = models.URLField(_('lien externe'), blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.title} ({self.get_file_type_display()})"

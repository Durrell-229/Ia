import uuid
import os
from django.db import models
from django.conf import settings
from django.utils import timezone


def document_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    return f"documents/{instance.owner.id}/{uuid.uuid4().hex}.{ext}"


class Document(models.Model):
    class Category(models.TextChoices):
        COURSE = 'course', 'Cours'
        EXAM = 'exam', 'Examen'
        RESOURCE = 'resource', 'Ressource'
        PERSONAL = 'personal', 'Personnel'
        SHARED = 'shared', 'Partagé'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField('Titre', max_length=255)
    description = models.TextField('Description', blank=True)
    file = models.FileField('Fichier', upload_to=document_upload_path)
    file_size = models.IntegerField('Taille (bytes)', default=0)
    file_type = models.CharField('Type', max_length=50, blank=True)
    category = models.CharField('Catégorie', max_length=20, choices=Category.choices, default=Category.PERSONAL)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')
    shared_with = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='shared_documents')
    is_public = models.BooleanField('Public', default=False)
    download_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Document'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            ext = self.file.name.split('.')[-1].lower()
            self.file_type = ext
        super().save(*args, **kwargs)

    @property
    def file_size_display(self):
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class DocumentComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField('Commentaire')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Commentaire'
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.full_name} on {self.document.title}"

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class VideoAnnouncement(models.Model):
    class Category(models.TextChoices):
        PROMO = 'promo', 'Promotion'
        TUTORIAL = 'tutorial', 'Tutoriel'
        ANNOUNCEMENT = 'announcement', 'Annonce'
        TESTIMONIAL = 'testimonial', 'Témoignage'
        FEATURE = 'feature', 'Fonctionnalité'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField('Titre', max_length=255)
    description = models.TextField('Description', blank=True)
    video_file = models.FileField(
        'Vidéo', upload_to='showcase_videos/',
        help_text='Format MP4 recommandé, max 100MB'
    )
    thumbnail = models.ImageField(
        'Miniature', upload_to='showcase_thumbnails/',
        blank=True, null=True,
        help_text='Image de couverture (optionnel)'
    )
    category = models.CharField(
        'Catégorie', max_length=20, choices=Category.choices,
        default=Category.PROMO
    )
    order = models.IntegerField('Ordre d\'affichage', default=0)
    is_active = models.BooleanField('Active', default=True)
    auto_play = models.BooleanField('Jouer automatiquement', default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='showcase_videos',
        verbose_name='Créé par'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Annonce Vidéo'
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"

    @property
    def video_url(self):
        if self.video_file:
            return self.video_file.url
        return ''

    @property
    def thumbnail_url(self):
        if self.thumbnail:
            return self.thumbnail.url
        return ''

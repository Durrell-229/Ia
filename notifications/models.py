"""
Système de Notifications Intelligentes Style Discord
Notifications push, in-app, avec designs professionnels et animations
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class NotificationCategory(models.Model):
    """Catégories de notifications pour filtrage et organisation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(_('nom'), max_length=100)
    icone = models.CharField(_('icône emoji'), max_length=10, default='🔔')
    couleur = models.CharField(
        _('couleur primaire'),
        max_length=7,
        default='#5865F2',  # Discord blurple
        help_text="Hex code sans #"
    )
    ordre = models.PositiveIntegerField(_('ordre affichage'), default=0)
    est_active = models.BooleanField(_('actif'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('catégorie notification')
        verbose_name_plural = _('catégories notifications')
        ordering = ['ordre']

    def __str__(self):
        return f"{self.icone} {self.nom}"


class Notification(models.Model):
    """
    Notification intelligente avec design style Discord
    Supporte différents types, actions personnalisées, et envoi push
    """
    class Priorité(models.TextChoices):
        BAS = 'low', _('Basse 🟢')
        NORMALE = 'normal', _('Normale 🔵')
        HAUTE = 'high', _('Haute 🟠')
        URGENTE = 'urgent', _('Urgente 🔴')
        CRITIQUE = 'critical', _('Critique ⭐')

    class Type(models.TextChoices):
        GENERAL = 'general', _('Général')
        EXAMEN = 'examen', _('Examen/Composition')
        NOTE = 'note', _('Note/Résultat')
        BADGE = 'badge', _('Badge/Récompense')
        COMMENTAIRE = 'commentaire', _('Commentaire')
        MENTION = 'mention', _('Mention sociale')
        SYSTEME = 'systeme', _('Système')
        PERSONNEL = 'personnel', _('Personnel')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Destinataire
    destinateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications_recues',
        null=True,  # NULL pour notifications publiques/générales
        blank=True
    )
    
    # Contenu
    titre = models.CharField(_('titre'), max_length=200)
    message = models.TextField(_('message'))
    description_longue = models.TextField(
        _('description détaillée'),
        blank=True,
        null=True,
        help_text="Contenu enrichi (HTML/formaté)"
    )
    
    # Design & Presentation
    type_notif = models.CharField(_('type'), max_length=20, choices=Type.choices, default=Type.GENERAL)
    priorite = models.CharField(_('priorité'), max_length=10, choices=Priorité.choices, default=Priorité.NORMALE)
    categorie = models.ForeignKey(
        NotificationCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    # Action custom (bouton principal)
    action_type = models.CharField(_('action type'), max_length=50, blank=True, null=True)
    action_url = models.URLField(_('url action'), blank=True, null=True)
    action_label = models.CharField(_('label bouton'), max_length=50, default='Voir')
    
    # Media attachment (image, fichier)
    image_url = models.URLField(_('URL image'), blank=True, null=True)
    video_url = models.URLField(_('URL vidéo'), blank=True, null=True)
    
    # Tracking
    is_read = models.BooleanField(_('lu'), default=False)
    is_pinned = models.BooleanField(_('épinglée'), default=False)
    is_deleted_for_user = models.BooleanField(_('supprimée pour moi'), default=False)
    
    # Metadata
    extra_data = models.JSONField(_('données supplémentaires'), default=dict, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    read_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # Expiration auto-suppression
    
    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['destinateur', 'is_read']),
            models.Index(fields=['destinateur', 'is_pinned']),
            models.Index(fields=['type_notif', '-created_at']),
        ]

    def __str__(self):
        return f"[{self.get_priorite_display()}] {self.titre}"
    
    @property
    def urgency_color(self):
        """Couleur selon la priorité"""
        colors = {
            self.Priorité.BAS: 'success',      # Green
            self.Priorité.NORMALE: 'primary',  # Blue
            self.Priorité.HAUTE: 'warning',    # Orange
            self.Priorité.URGENTE: 'danger',   # Red
            self.Priorité.CRITIQUE: 'critical' # Purple/Gold
        }
        return colors.get(self.priorite, 'primary')
    
    @property
    def time_ago(self):
        """Formatage temps écoulé (à l'instar Discord)"""
        from django.utils.timezone import now
        from datetime import timedelta
        
        delta = now() - self.created_at
        
        if delta < timedelta(seconds=60):
            return "À l'instant"
        elif delta < timedelta(minutes=60):
            minutes = int(delta.seconds // 60)
            return f"Il y a {minutes} minute{'s' if minutes > 1 else ''}"
        elif delta < timedelta(hours=60):
            hours = int(delta.total_seconds() // 3600)
            return f"Il y a {hours} heure{'s' if hours > 1 else ''}"
        elif delta < timedelta(days=30):
            days = int(delta.total_seconds() // 86400)
            return f"Il y a {days} jour{'s' if days > 1 else ''}"
        else:
            return self.created_at.strftime("%d %b %Y")
    
    @property
    def icon_style(self):
        """Style d'icône selon le type"""
        icons = {
            self.Type.GENERAL: 'fa-bullhorn',
            self.Type.EXAMEN: 'fa-file-alt',
            self.Type.NOTE: 'fa-chart-line',
            self.Type.BADGE: 'fa-trophy',
            self.Type.COMMENTAIRE: 'fa-comment',
            self.Type.MENTION: 'fa-user-friends',
            self.Type.SYSTEME: 'fa-cog',
            self.Type.PERSONNEL: 'fa-user-circle',
        }
        return icons.get(self.type_notif, 'fa-bell')
    
    def marquer_comme_lue(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])


class NotificationSetting(models.Model):
    """Préférences utilisateur pour les notifications"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Enable/disable par type
    enabled_types = models.JSONField(default=dict)  # {'examens': True, 'notes': False}
    
    # Sons
    son_notifications = models.BooleanField(default=True)
    son_silencieux_heures = models.CharField(max_length=20, blank=True, null=True)
    son_heures_reprise = models.CharField(max_length=20, blank=True, null=True)
    
    # Push notifications
    push_enabled = models.BooleanField(default=True)
    push_browser_id = models.TextField(blank=True, null=True)
    push_subscription = models.TextField(blank=True, null=True, help_text="Subscription VAPID JSON")
    
    # Email notifications
    email_digest_daily = models.BooleanField(default=False)
    email_digest_weekly = models.BooleanField(default=False)
    
    # Mode Do Not Disturb
    do_not_disturb = models.BooleanField(default=False)
    dnd_start_time = models.TimeField(null=True, blank=True)
    dnd_end_time = models.TimeField(null=True, blank=True)
    
    # Auto-dismiss
    auto_dismiss_unread = models.BooleanField(default=False)
    auto_dismiss_minutes = models.PositiveIntegerField(default=300)  # 5 min par défaut
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('paramètre notification')
        verbose_name_plural = _('paramètres notifications')


# ===========================================================================
# Système de Template de Notification (pour admin)
# ===========================================================================

class NotificationTemplate(models.Model):
    """
    Templates de notifications réutilisables pour administration
    Avec variables dynamiques et styles intégrés
    """
    class Layout(models.TextChoices):
        SIMPLE = 'simple', _('Simple')
        CARD = 'card', _('Carte Discord')
        RICH = 'rich', _('Riche')
        EMBED = 'embed', _('Embed')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(_('nom'), max_length=200)
    slug = models.SlugField(unique=True)
    
    layout = models.CharField(_('layout'), max_length=20, choices=Layout.choices, default=Layout.CARD)
    
    # Contenu template (variables remplacées)
    titre_template = models.TextField(help_text="Utilisez {{ variable }} pour variables dynamiques")
    message_template = models.TextField()
    
    # Variables acceptées
    variables_acceptees = models.JSONField(default=list)
    
    # Design options
    accent_color = models.CharField(max_length=7, default='#5865F2')
    show_timestamp = models.BooleanField(default=True)
    show_avatar = models.BooleanField(default=True)
    
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('template notification')
        verbose_name_plural = _('templates notifications')
        ordering = ['nom']

    def render_notification(self, variables_dict, recipient=None):
        """Rend une notification à partir du template avec variables"""
        titre = self.titre_template.format(**variables_dict)
        message = self.message_template.format(**variables_dict)

        return Notification.objects.create(
            destinateur=recipient,
            titre=titre,
            message=message,
            extra_data={'template_id': str(self.id), 'variables': variables_dict},
        )


class EmailQueue(models.Model):
    """
    File d'attente d'emails pour envoi asynchrone
    Permet de queue les emails et gérer les tentatives/réessais
    """
    class Statut(models.TextChoices):
        EN_ATTENTE = 'pending', _('En attente ⏳')
        EN_COURS = 'sending', _('En cours d\'envoi 📤')
        ENVOYE = 'sent', _('Envoyé ✅')
        ECHEC = 'failed', _('Échoué ❌')
        ANNULE = 'cancelled', _('Annulé 🚫')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Destinataire
    destinataire = models.EmailField(_('destinataire'))
    cc = models.EmailField(_('CC'), blank=True, null=True)
    bcc = models.EmailField(_('BCC'), blank=True, null=True)

    # Contenu
    sujet = models.CharField(_('sujet'), max_length=300)
    body_html = models.TextField(_('contenu HTML'), blank=True, null=True)
    body_text = models.TextField(_('contenu texte'), blank=True, null=True)

    # Tracking
    statut = models.CharField(_('statut'), max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    tentatives = models.PositiveIntegerField(_('tentatives'), default=0)
    max_tentatives = models.PositiveIntegerField(_('max tentatives'), default=3)
    derniere_erreur = models.TextField(_('dernière erreur'), blank=True, null=True)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    envoi_apres = models.DateTimeField(_('envoyer après'), null=True, blank=True,
                                       help_text="Différer l'envoi à une date précise")
    envoye_a = models.DateTimeField(_('envoyé à'), null=True, blank=True)

    class Meta:
        verbose_name = _('file email')
        verbose_name_plural = _('file emails')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['statut', '-created_at']),
            models.Index(fields=['envoi_apres', 'statut']),
        ]

    def __str__(self):
        return f"[{self.get_statut_display()}] {self.sujet} → {self.destinataire}"

    def peut_retry(self):
        """Vérifie si on peut encore réessayer l'envoi"""
        return self.tentatives < self.max_tentatives and self.statut != self.Statut.ANNULE

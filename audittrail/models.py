import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class AuditLog(models.Model):
    """Journal d'audit complet : traçabilité de toutes les actions."""
    class ActionType(models.TextChoices):
        CREATE = 'create', _('Création')
        UPDATE = 'update', _('Modification')
        DELETE = 'delete', _('Suppression')
        LOGIN = 'login', _('Connexion')
        LOGOUT = 'logout', _('Déconnexion')
        SUBMIT = 'submit', _('Soumission')
        CORRECT = 'correct', _('Correction')
        EXPORT = 'export', _('Export')
        DOWNLOAD = 'download', _('Téléchargement')
        CHEAT = 'cheat', _('Tentative de triche')
        ASSIGN = 'assign', _('Attribution')
        VERIFY = 'verify', _('Vérification')

    class Severity(models.TextChoices):
        INFO = 'info', _('Info')
        WARNING = 'warning', _('Attention')
        CRITICAL = 'critical', _('Critique')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(_('action'), max_length=20, choices=ActionType.choices)
    severity = models.CharField(_('sévérité'), max_length=20, choices=Severity.choices, default=Severity.INFO)
    resource_type = models.CharField(_('type de ressource'), max_length=50)
    resource_id = models.CharField(_('ID ressource'), max_length=100, blank=True)
    description = models.TextField(_('description'))
    details = models.JSONField(_('détails'), default=dict)
    ip_address = models.GenericIPAddressField(_('adresse IP'), blank=True, null=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    session_id = models.CharField(_('session ID'), max_length=100, blank=True)
    timestamp = models.DateTimeField(_('horodatage'), auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _('journal d\'audit')
        verbose_name_plural = _('journal d\'audit')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]

    def __str__(self):
        return f"[{self.get_action_display()}] {self.description[:80]}"


class DataExport(models.Model):
    """Suivi des exports de données."""
    class FormatExport(models.TextChoices):
        CSV = 'csv', _('CSV')
        EXCEL = 'excel', _('Excel')
        PDF = 'pdf', _('PDF')
        JSON = 'json', _('JSON')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    demandeur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='data_exports')
    type_export = models.CharField(_('type d\'export'), max_length=50)
    format_export = models.CharField(_('format'), max_length=10, choices=FormatExport.choices)
    fichier = models.FileField(_('fichier'), upload_to='exports/%Y/%m/', blank=True, null=True)
    parametres = models.JSONField(_('paramètres'), default=dict)
    nb_lignes = models.PositiveIntegerField(_('nombre de lignes'), default=0)
    statut = models.CharField(_('statut'), max_length=20, default='en_cours')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _('export de données')
        verbose_name_plural = _('exports de données')
        ordering = ['-created_at']

    def __str__(self):
        return f"Export {self.type_export} ({self.format_export}) - {self.demandeur}"

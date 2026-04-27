import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from compositions.models import Resultat


class AICorrection(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente')
        EN_COURS = 'en_cours', _('En cours')
        TERMINE = 'termine', _('Terminé')
        ERREUR = 'erreur', _('Erreur')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resultat = models.OneToOneField(Resultat, on_delete=models.CASCADE, related_name='ai_correction')
    corrige_type_text = models.TextField(_('texte du corrigé type'), blank=True)
    copie_text = models.TextField(_('texte de la copie'), blank=True)
    prompt_envoye = models.TextField(_('prompt envoyé'), blank=True)
    reponse_ia = models.TextField(_('réponse IA'), blank=True)
    note_proposee = models.DecimalField(_('note proposée'), max_digits=5, decimal_places=2, blank=True, null=True)
    details_json = models.JSONField(_('détails JSON'), default=dict)
    model_utilise = models.CharField(_('modèle utilisé'), max_length=50, blank=True)
    tokens_utilises = models.PositiveIntegerField(_('tokens utilisés'), default=0)
    statut = models.CharField(_('statut'), max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    erreur = models.TextField(_('erreur'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('correction IA')
        verbose_name_plural = _('corrections IA')
        ordering = ['-created_at']

    def __str__(self):
        return f"Correction IA - {self.resultat.session.eleve.full_name}"


class CorrectionDetail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ai_correction = models.ForeignKey(AICorrection, on_delete=models.CASCADE, related_name='details')
    question_number = models.PositiveIntegerField(_('numéro de question'))
    note_partielle = models.DecimalField(_('note partielle'), max_digits=5, decimal_places=2)
    commentaire = models.TextField(_('commentaire'))
    erreurs = models.JSONField(_('erreurs identifiées'), default=list)
    points_forts = models.JSONField(_('points forts'), default=list)

    class Meta:
        verbose_name = _('détail de correction')
        verbose_name_plural = _('détails de correction')
        ordering = ['question_number']

    def __str__(self):
        return f"Q{self.question_number} - {self.ai_correction}"

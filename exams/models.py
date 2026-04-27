import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from core.models import Matiere, Classe


class Exam(models.Model):
    class Type(models.TextChoices):
        COMPOSITION = 'composition', _('Composition')
        EXAMEN = 'examen', _('Examen')
        DEVOIR = 'devoir', _('Devoir')
        CONCOURS = 'concours', _('Concours')
        EVALUATION_PROF = 'eval_prof', _('Évaluation Professeur')

    class Statut(models.TextChoices):
        BROUILLON = 'brouillon', _('Brouillon')
        PUBLIE = 'publie', _('Publié')
        EN_COURS = 'en_cours', _('En cours')
        TERMINE = 'termine', _('Terminé')
        ANNULE = 'annule', _('Annulé')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titre = models.CharField(_('titre'), max_length=300)
    description = models.TextField(_('description'), blank=True)
    type_exam = models.CharField(_('type'), max_length=20, choices=Type.choices, default=Type.COMPOSITION)
    matiere = models.ForeignKey(Matiere, on_delete=models.SET_NULL, null=True, related_name='exams')
    classe = models.ForeignKey(Classe, on_delete=models.SET_NULL, null=True, blank=True, related_name='exams')
    createur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exams_crees')
    duree_minutes = models.PositiveIntegerField(_('durée (minutes)'), default=60)
    date_debut = models.DateTimeField(_('date de début'))
    date_fin = models.DateTimeField(_('date de fin'))
    note_maximale = models.DecimalField(_('note maximale'), max_digits=5, decimal_places=2, default=20.00)
    coefficient = models.DecimalField(_('coefficient'), max_digits=4, decimal_places=2, default=1.00)
    statut = models.CharField(_('statut'), max_length=20, choices=Statut.choices, default=Statut.BROUILLON)
    approval_status = models.CharField(_('statut approbation'), max_length=20, choices=[('pending', 'En attente'), ('approved', 'Approuvé'), ('rejected', 'Rejeté')], default='pending')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='exams_approved')
    est_public = models.BooleanField(_('public'), default=False)
    instructions = models.TextField(_('instructions'), blank=True)
    anti_cheat_active = models.BooleanField(_('anti-triche actif'), default=True)
    camera_required = models.BooleanField(_('caméra obligatoire'), default=True)
    fullscreen_required = models.BooleanField(_('plein écran obligatoire'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('épreuve')
        verbose_name_plural = _('épreuves')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.titre} ({self.get_type_exam_display()})"

    @property
    def is_en_cours(self):
        now = timezone.now()
        return self.date_debut <= now <= self.date_fin and self.statut == self.Statut.EN_COURS

    @property
    def is_passe(self):
        return timezone.now() > self.date_fin


class ExamFile(models.Model):
    class TypeFichier(models.TextChoices):
        EPREUVE = 'epreuve', _('Épreuve')
        CORRIGE_TYPE = 'corrige_type', _('Corrigé Type')
        ANNEXE = 'annexe', _('Annexe')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='files')
    type_fichier = models.CharField(_('type de fichier'), max_length=20, choices=TypeFichier.choices)
    fichier = models.FileField(_('fichier'), upload_to='exams/%Y/%m/')
    nom_original = models.CharField(_('nom original'), max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('fichier d\'épreuve')
        verbose_name_plural = _('fichiers d\'épreuve')

    def __str__(self):
        return f"{self.nom_original} ({self.get_type_fichier_display()})"


class ExamAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='assignments')
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exam_assignments', blank=True, null=True)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='exam_assignments', blank=True, null=True)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='assignments_crees')
    assigned_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)

    class Meta:
        unique_together = [['exam', 'eleve'], ['exam', 'classe']]
        verbose_name = _('attribution d\'épreuve')
        verbose_name_plural = _('attributions d\'épreuves')

    def __str__(self):
        target = self.eleve or self.classe
        return f"{self.exam.titre} -> {target}"

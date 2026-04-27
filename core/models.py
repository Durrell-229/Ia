import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


from core.constants import MATIERE_CHOICES

class Matiere(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(_('nom'), max_length=200, choices=MATIERE_CHOICES)
    code = models.CharField(_('code'), max_length=20, unique=True)
    description = models.TextField(_('description'), blank=True)
    niveaux = models.JSONField(_('niveaux concernés'), default=list)
    couleur = models.CharField(_('couleur'), max_length=7, default='#6366F1')
    icone = models.CharField(_('icône'), max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('matière')
        verbose_name_plural = _('matières')
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Classe(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(_('nom'), max_length=200)
    niveau = models.CharField(_('niveau'), max_length=20)
    section = models.CharField(_('section / filière'), max_length=100, blank=True)
    annee_academique = models.CharField(_('année académique'), max_length=20)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('classe')
        verbose_name_plural = _('classes')
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.annee_academique})"


class Parametre(models.Model):
    cle = models.CharField(max_length=100, unique=True)
    valeur = models.TextField()
    description = models.TextField(blank=True)

    def __str__(self):
        return self.cle


class Feedback(models.Model):
    """Feedback élève vers professeur ou professeur vers élève."""
    class Type(models.TextChoices):
        ELEVE_PROF = 'eleve_prof', _('Élève → Professeur')
        PROF_ELEVE = 'prof_eleve', _('Professeur → Élève')
        ELEVE_PLATEFORME = 'eleve_plateforme', _('Élève → Plateforme')

    class Note(models.IntegerChoices):
        TRES_MAUVAIS = 1, _('Très mauvais')
        MAUVAIS = 2, _('Mauvais')
        MOYEN = 3, _('Moyen')
        BON = 4, _('Bon')
        EXCELLENT = 5, _('Excellent')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expediteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feedbacks_envoyes')
    destinataire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks_recus')
    type_feedback = models.CharField(_('type'), max_length=20, choices=Type.choices, default=Type.ELEVE_PROF)
    note = models.IntegerField(_('note'), choices=Note.choices, default=Note.BON)
    commentaire = models.TextField(_('commentaire'))
    examen = models.ForeignKey('exams.Exam', on_delete=models.SET_NULL, null=True, blank=True)
    est_anonyme = models.BooleanField(_('anonyme'), default=False)
    est_public = models.BooleanField(_('public'), default=False)
    est_lu = models.BooleanField(_('lu'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('feedback')
        verbose_name_plural = _('feedbacks')
        ordering = ['-created_at']

    def __str__(self):
        sender = 'Anonyme' if self.est_anonyme else self.expediteur.full_name
        return f"Feedback {self.get_type_feedback_display()} par {sender}"


class CalendarEvent(models.Model):
    """Événements du calendrier d'examens."""
    class TypeEvenement(models.TextChoices):
        EXAMEN = 'examen', _('Examen')
        COMPOSITION = 'composition', _('Composition')
        CORRECTION = 'correction', _('Séance de correction')
        RATTRAPAGE = 'rattrapage', _('Rattrapage')
        AUTRE = 'autre', _('Autre')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titre = models.CharField(_('titre'), max_length=255)
    type_evenement = models.CharField(_('type'), max_length=20, choices=TypeEvenement.choices, default=TypeEvenement.COMPOSITION)
    description = models.TextField(_('description'), blank=True)
    date_debut = models.DateTimeField(_('début'))
    date_fin = models.DateTimeField(_('fin'))
    lieu = models.CharField(_('lieu'), max_length=255, blank=True)
    salle = models.CharField(_('salle'), max_length=100, blank=True)
    examen = models.ForeignKey('exams.Exam', on_delete=models.SET_NULL, null=True, blank=True)
    createur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calendar_events')
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='calendar_participations', blank=True)
    couleur = models.CharField(_('couleur'), max_length=7, default='#6366F1')
    est_public = models.BooleanField(_('public'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('événement calendrier')
        verbose_name_plural = _('événements calendrier')
        ordering = ['date_debut']

    def __str__(self):
        return f"{self.titre} - {self.date_debut.strftime('%d/%m/%Y')}"

import uuid
import difflib
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class PlagiarismCheck(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente')
        EN_COURS = 'en_cours', _('En cours')
        TERMINE = 'termine', _('Terminé')
        ERREUR = 'erreur', _('Erreur')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey('exams.Exam', on_delete=models.CASCADE, related_name='plagiarism_checks')
    declenche_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    statut = models.CharField(_('statut'), max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    seuil_similarite = models.DecimalField(_('seuil similarite (%)'), max_digits=5, decimal_places=2, default=75.0)
    nb_paires_analysees = models.PositiveIntegerField(_('paires analysées'), default=0)
    nb_paires_suspectes = models.PositiveIntegerField(_('paires suspectes'), default=0)
    rapport_global = models.JSONField(_('rapport global'), default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _('vérification plagiat')
        verbose_name_plural = _('vérifications plagiat')
        ordering = ['-created_at']

    def __str__(self):
        return f"Plagiat - {self.exam.titre}"


class PlagiarismPair(models.Model):
    class NiveauSuspection(models.TextChoices):
        FAIBLE = 'faible', _('Faible (<30%)')
        MODERE = 'modere', _('Modéré (30-60%)')
        ELEVE = 'eleve', _('Élevé (60-80%)')
        CRITIQUE = 'critique', _('Critique (>80%)')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    verification = models.ForeignKey(PlagiarismCheck, on_delete=models.CASCADE, related_name='pairs')
    session_1 = models.ForeignKey('compositions.CompositionSession', on_delete=models.CASCADE, related_name='plagiarism_as_1')
    session_2 = models.ForeignKey('compositions.CompositionSession', on_delete=models.CASCADE, related_name='plagiarism_as_2')
    similarite_globale = models.DecimalField(_('similarité (%)'), max_digits=5, decimal_places=2, default=0)
    similarite_par_question = models.JSONField(_('similarité par question'), default=dict)
    niveau_suspection = models.CharField(_('niveau'), max_length=20, choices=NiveauSuspection.choices, default=NiveauSuspection.FAIBLE)
    phrases_communes = models.JSONField(_('phrases communes'), default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('paire plagiat')
        verbose_name_plural = _('paires plagiat')
        unique_together = ['verification', 'session_1', 'session_2']
        ordering = ['-similarite_globale']

    def __str__(self):
        return f"{self.session_1.eleve.full_name} vs {self.session_2.eleve.full_name} ({self.similarite_globale}%)"

    @staticmethod
    def compute_similarity(text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0
        t1 = text1.lower().strip().split()
        t2 = text2.lower().strip().split()
        if not t1 or not t2:
            return 0.0
        ratio = difflib.SequenceMatcher(None, t1, t2).ratio()
        return round(ratio * 100, 2)

    @staticmethod
    def find_common_phrases(text1: str, text2: str, min_words: int = 5) -> list:
        phrases = []
        for s1 in text1.lower().split('.'):
            s1 = s1.strip()
            if len(s1.split()) < min_words:
                continue
            for s2 in text2.lower().split('.'):
                s2 = s2.strip()
                if len(s2.split()) < min_words:
                    continue
                ratio = difflib.SequenceMatcher(None, s1, s2).ratio()
                if ratio > 0.8:
                    phrases.append({'phrase1': s1[:200], 'phrase2': s2[:200], 'similarite': round(ratio * 100, 2)})
        return phrases[:20]


class PlagiarismReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    verification = models.OneToOneField(PlagiarismCheck, on_delete=models.CASCADE, related_name='report')
    pdf = models.FileField(_('PDF'), upload_to='plagiarism_reports/%Y/%m/', blank=True, null=True)
    resume = models.TextField(_('résumé'), blank=True)
    recommendations = models.TextField(_('recommandations'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('rapport plagiat')
        verbose_name_plural = _('rapports plagiat')

import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class QuestionBank(models.Model):
    """Banque de questions QCM réutilisable."""
    class Difficulte(models.TextChoices):
        FACILE = 'facile', _('Facile')
        MOYEN = 'moyen', _('Moyen')
        DIFFICILE = 'difficile', _('Difficile')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    matiere = models.ForeignKey('core.Matiere', on_delete=models.SET_NULL, null=True, related_name='questions')
    createur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='questions_creees')
    texte = models.TextField(_('texte de la question'))
    explication = models.TextField(_('explication'), blank=True)
    difficulte = models.CharField(_('difficulté'), max_length=20, choices=Difficulte.choices, default=Difficulte.MOYEN)
    tags = models.JSONField(_('tags'), default=list)
    est_publique = models.BooleanField(_('publique'), default=False)
    generee_par_ia = models.BooleanField(_('générée par IA'), default=False)
    source_cours = models.TextField(_('source du cours'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('banque de questions')
        verbose_name_plural = _('banques de questions')
        ordering = ['-created_at']

    def __str__(self):
        return self.texte[:80]


class Choice(models.Model):
    """Choix de réponse pour une question QCM."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name='choices')
    texte = models.TextField(_('texte du choix'))
    est_correct = models.BooleanField(_('est correct'), default=False)
    ordre = models.PositiveIntegerField(_('ordre'), default=0)
    explication = models.TextField(_('explication'), blank=True)

    class Meta:
        verbose_name = _('choix')
        verbose_name_plural = _('choix')
        ordering = ['ordre']

    def __str__(self):
        return f"{'✓' if self.est_correct else '✗'} {self.texte[:50]}"


class QCMExam(models.Model):
    """Examen QCM avec paramètres avancés."""
    class ModeNotation(models.TextChoices):
        CLASSIQUE = 'classique', _('Classique (bonne réponse = points)')
        PENALITE = 'penalite', _('Avec pénalité (mauvaise réponse = -points)')
        PARTIELLE = 'partielle', _('Partielle (réponses partielles)')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.OneToOneField('exams.Exam', on_delete=models.CASCADE, related_name='qcm_config')
    melanger_questions = models.BooleanField(_('mélanger questions'), default=True)
    melanger_choix = models.BooleanField(_('mélanger choix'), default=True)
    afficher_resultat_immediat = models.BooleanField(_('résultat immédiat'), default=False)
    mode_notation = models.CharField(_('mode de notation'), max_length=20, choices=ModeNotation.choices, default=ModeNotation.CLASSIQUE)
    points_bonne_reponse = models.DecimalField(_('points bonne réponse'), max_digits=4, decimal_places=2, default=1.0)
    penalite_mauvaise_reponse = models.DecimalField(_('pénalité mauvaise réponse'), max_digits=4, decimal_places=2, default=0.0)
    nb_questions_par_page = models.PositiveIntegerField(_('questions par page'), default=1)

    class Meta:
        verbose_name = _('configuration QCM')
        verbose_name_plural = _('configurations QCM')

    def __str__(self):
        return f"QCM Config - {self.exam.titre}"


class QCMExamQuestion(models.Model):
    """Association question-examen QCM."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    qcm_exam = models.ForeignKey(QCMExam, on_delete=models.CASCADE, related_name='exam_questions')
    question = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name='exam_associations')
    ordre = models.PositiveIntegerField(_('ordre'), default=0)
    points = models.DecimalField(_('points'), max_digits=4, decimal_places=2, default=1.0)

    class Meta:
        verbose_name = _('question d\'examen QCM')
        verbose_name_plural = _('questions d\'examen QCM')
        ordering = ['ordre']

    def __str__(self):
        return f"Q{self.ordre} - {self.qcm_exam.exam.titre}"


class QCMAnswer(models.Model):
    """Réponse d'un élève à une question QCM."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey('compositions.CompositionSession', on_delete=models.CASCADE, related_name='qcm_answers')
    question = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name='student_answers')
    choix_selectionnes = models.JSONField(_('choix sélectionnés'), default=list)
    est_correct = models.BooleanField(_('est correct'), default=False)
    points_obtenus = models.DecimalField(_('points obtenus'), max_digits=4, decimal_places=2, default=0)
    temps_reponse_secondes = models.PositiveIntegerField(_('temps de réponse (s)'), default=0)
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('réponse QCM')
        verbose_name_plural = _('réponses QCM')
        unique_together = ['session', 'question']

    def __str__(self):
        return f"{self.session.eleve.full_name} - Q{self.question.id.hex[:8]}"

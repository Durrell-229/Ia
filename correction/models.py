from django.db import models
import uuid
from django.conf import settings
from exams.models import Exam

class StatutCorrection(models.TextChoices):
    EN_ATTENTE = 'pending', 'En attente'
    VALIDATION_ENSEIGNANT = 'corrected', 'Corrigé'
    APPROUVE = 'approved', 'Approuvé'

class CorrectionCopie(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='submissions', null=True, blank=True)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    image = models.ImageField(upload_to='submissions/%Y/%m/', blank=True, null=True)
    corrected_text = models.TextField(blank=True, null=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)
    note_ia = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    json_resultat = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=StatutCorrection.choices, default=StatutCorrection.EN_ATTENTE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.email} - {self.exam.titre if self.exam else 'QCM'}"

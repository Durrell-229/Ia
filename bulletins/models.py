import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Bulletin(models.Model):
    class Periode(models.TextChoices):
        TRIMESTRE_1 = 'T1', _('1er Trimestre')
        TRIMESTRE_2 = 'T2', _('2ème Trimestre')
        TRIMESTRE_3 = 'T3', _('3ème Trimestre')
        SEMESTRE_1 = 'S1', _('1er Semestre')
        SEMESTRE_2 = 'S2', _('2ème Semestre')
        ANNUEL = 'AN', _('Annuel')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bulletins')
    classe = models.CharField(max_length=100)
    annee_scolaire = models.CharField(max_length=20)
    periode = models.CharField(max_length=5, choices=Periode.choices)
    
    # Données IA & Académiques
    moyenne_generale = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    rang = models.PositiveIntegerField(default=1)
    appreciation_ia = models.TextField(_('synthèse pédagogique IA'), blank=True, default="")
    
    # Référence examen/QCM associé
    qcm_reference = models.ForeignKey('qcm.QCMExam', on_delete=models.SET_NULL, null=True, blank=True, related_name='bulletins')
    composition_reference = models.ForeignKey('compositions.CompositionSession', on_delete=models.SET_NULL, null=True, blank=True, related_name='bulletins')
    
    # Sécurité & Légalité
    signature_numerique = models.CharField(max_length=255, blank=True)
    verification_token = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    is_signed = models.BooleanField(default=False)
    file_pdf = models.FileField(upload_to='bulletins_officiels/%Y/%m/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bulletin {self.periode} - {self.eleve.full_name}"

class BulletinLigne(models.Model):
    bulletin = models.ForeignKey(Bulletin, on_delete=models.CASCADE, related_name='lignes')
    matiere = models.CharField(max_length=100)
    note = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    note_max = models.DecimalField(max_digits=5, decimal_places=2, default=20.0)
    moyenne_classe = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    appreciation = models.TextField(blank=True, default="")

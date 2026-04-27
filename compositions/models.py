import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from exams.models import Exam


class CompositionSession(models.Model):
    class Mode(models.TextChoices):
        EN_LIGNE = 'en_ligne', _('En Ligne')
        SUR_PAPIER = 'sur_papier', _('Sur Papier')

    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', _('En attente')
        EN_COURS = 'en_cours', _('En cours')
        SOUMIS = 'soumis', _('Soumis')
        EN_CORRECTION = 'en_correction', _('En correction')
        CORRIGE = 'corrige', _('Corrigé')
        EXCLU = 'exclu', _('Exclu (triche)')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='sessions')
    eleve = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='composition_sessions')
    mode = models.CharField(_('mode'), max_length=20, choices=Mode.choices, default=Mode.EN_LIGNE)
    statut = models.CharField(_('statut'), max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    started_at = models.DateTimeField(_('début'), blank=True, null=True)
    submitted_at = models.DateTimeField(_('soumission'), blank=True, null=True)
    time_spent_seconds = models.PositiveIntegerField(_('temps passé (secondes)'), default=0)
    qr_code = models.ImageField(_('QR Code'), upload_to='qr_codes/', blank=True, null=True)
    qr_token = models.CharField(_('token QR'), max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    cheat_count = models.PositiveIntegerField(_('nombre de triches'), default=0)
    cheat_logs = models.JSONField(_('logs de triche'), default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('session de composition')
        verbose_name_plural = _('sessions de composition')
        unique_together = ['exam', 'eleve']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.eleve.full_name} - {self.exam.titre}"

    def start(self):
        self.statut = self.Statut.EN_COURS
        self.started_at = timezone.now()
        self.save()

    def submit(self):
        self.statut = self.Statut.SOUMIS
        self.submitted_at = timezone.now()
        if self.started_at:
            self.time_spent_seconds = int((timezone.now() - self.started_at).total_seconds())
        self.save()


class StudentAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(CompositionSession, on_delete=models.CASCADE, related_name='answers')
    question_number = models.PositiveIntegerField(_('numéro de question'))
    content = models.TextField(_('contenu de la réponse'))
    file = models.FileField(_('fichier joint'), upload_to='answers/%Y/%m/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('réponse de l\'élève')
        verbose_name_plural = _('réponses des élèves')
        unique_together = ['session', 'question_number']
        ordering = ['question_number']

    def __str__(self):
        return f"Q{self.question_number} - {self.session}"


class StudentSubmissionFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(CompositionSession, on_delete=models.CASCADE, related_name='submission_files')
    fichier = models.ImageField(_('fichier'), upload_to='submissions/%Y/%m/')
    page_number = models.PositiveIntegerField(_('numéro de page'), default=1)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('fichier de soumission')
        verbose_name_plural = _('fichiers de soumission')
        ordering = ['page_number']

    def __str__(self):
        return f"Page {self.page_number} - {self.session}"


class Resultat(models.Model):
    class Mention(models.TextChoices):
        EXCELLENT = 'excellent', _('Excellent')
        TRES_BIEN = 'tres_bien', _('Très Bien')
        BIEN = 'bien', _('Bien')
        ASSEZ_BIEN = 'assez_bien', _('Assez Bien')
        PASSABLE = 'passable', _('Passable')
        INSUFFISANT = 'insuffisant', _('Insuffisant')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField(CompositionSession, on_delete=models.CASCADE, related_name='resultat')
    note = models.DecimalField(_('note'), max_digits=5, decimal_places=2)
    note_sur = models.DecimalField(_('note sur'), max_digits=5, decimal_places=2, default=20.00)
    mention = models.CharField(_('mention'), max_length=20, choices=Mention.choices, blank=True)
    appreciation = models.TextField(_('appréciation'), blank=True)
    details_correction = models.JSONField(_('détails de correction'), default=dict)
    classement = models.PositiveIntegerField(_('classement'), default=0)
    total_participants = models.PositiveIntegerField(_('total participants'), default=0)
    corrige_par_ia = models.BooleanField(_('corrigé par IA'), default=False)
    corrige_par_humain = models.BooleanField(_('corrigé par humain'), default=False)
    corrigeur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='corrections_effectuees')
    corrige_at = models.DateTimeField(_('date de correction'), blank=True, null=True)
    bulletin_pdf = models.FileField(_('bulletin PDF'), upload_to='bulletins/%Y/%m/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('résultat')
        verbose_name_plural = _('résultats')
        ordering = ['-note']

    def __str__(self):
        return f"{self.session.eleve.full_name} - {self.note}/{self.note_sur}"

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from decimal import Decimal


@receiver(pre_save, sender=Resultat)
def set_mention_auto(sender, instance, **kwargs):
    """Détermine automatiquement la mention basée sur la note"""
    if instance.note is not None:
        note_val = float(instance.note)
        if note_val >= 16:
            instance.mention = 'excellent'
        elif note_val >= 14:
            instance.mention = 'tres_bien'
        elif note_val >= 12:
            instance.mention = 'bien'
        elif note_val >= 10:
            instance.mention = 'assez_bien'
        elif note_val >= 8:
            instance.mention = 'passable'
        else:
            instance.mention = 'insuffisant'


@receiver(post_save, sender=Resultat)
def trigger_bulletin_generation(sender, instance, created, **kwargs):
    """
    Génère automatiquement un bulletin PDF professionnel après chaque correction.
    Utilise l'orchestrateur IA pour une appréciation personnalisée.
    Lie le bulletin au QCM/examen correspondant.
    """
    if created and instance.note is not None and instance.note > 0:
        try:
            from bulletins.services import BulletinService
            from bulletins.models import Bulletin
            from ai_engine.orchestrator import SmartOrchestrator
            import logging
            from django.utils import timezone
            from decimal import Decimal
            
            logger = logging.getLogger(__name__)
            logger.info(f"[BulletinAuto] Démarrage génération pour resultat ID: {instance.id}")
            
            session = instance.session
            eleve = session.eleve
            
            # Calcul note moyenne (sur 20)
            note_float = float(instance.note)
            note_max_float = float(instance.note_sur)
            moyenne_norm = (note_float / note_max_float) * 20
            
            # Récupérer ou créer bulletin existant
            bulletin, created_bulletin = Bulletin.objects.get_or_create(
                eleve=eleve,
                periode='AN',
                annee_scolaire="2025-2026",
                defaults={
                    'classe': getattr(eleve, 'classe', 'Inconnue'),
                    'moyenne_generale': moyenne_norm,
                    'rang': getattr(instance, 'classement', 1),
                    'appreciation_ia': '',
                    'composition_reference': session,  # Lier session si présente
                }
            )
            
            # Mettre à jour le bulletin même si existant
            if not created_bulletin:
                bulletin.moyenne_generale = moyenne_norm
                bulletin.rang = getattr(instance, 'classement', 1)
            
            # Si session liée a examen avec qcm_config, lier aussi
            if hasattr(session, 'exam') and session.exam and hasattr(session.exam, 'qcm_config'):
                bulletin.qcm_reference = session.exam.qcm_config
            
            # Générer appréciation IA si pas encore présente
            appreciation_ia = instance.appreciation
            if not appreciation_ia and instance.details_correction:
                try:
                    orchestrator = SmartOrchestrator()
                    appreciation_ia = orchestrator.generate_appreciation_automatique(
                        moyenne_norm,
                        instance.details_correction
                    )
                    bulletin.appreciation_ia = appreciation_ia[:2000]  # Limite longueur
                except Exception as ia_error:
                    logger.warning(f"[BulletinAuto] Échec génération IA: {ia_error}")
                    appreciation_ia = f"Note obtenue : {moyenne_norm}/20. Continuez vos efforts !"
            
            # Sauvegarder avant génération PDF
            bulletin.save(update_fields=['moyenne_generale', 'appreciation_ia'])
            
            # Créer lignes détaillées
            from bulletins.models import BulletinLigne
            BulletinLigne.objects.filter(bulletin=bulletin).delete()
            
            # Ajouter matière principale
            matiere_name = getattr(getattr(session, 'exam', None), 'matiere', 'QCM - Évaluation Générale')
            
            BulletinLigne.objects.create(
                bulletin=bulletin,
                matiere=matiere_name,
                note=moyenne_norm,
                note_max=Decimal('20.00'),
                moyenne_classe=moyenne_norm,
                appreciation=appreciation_ia or '-'
            )
            
            # Si détails disponibles, ajouter sous-sections
            details = instance.details_correction.get('details', [])
            for idx, detail in enumerate(details[:5]):  # Max 5 détails
                BulletinLigne.objects.create(
                    bulletin=bulletin,
                    matiere=f"{matiere_name} - Question {idx+1}",
                    note=detail.get('points_obtenus', 0),
                    note_max=Decimal(str(detail.get('points_max', 5))),
                    moyenne_classe=(float(detail.get('points_obtenus', 0)) / detail.get('points_max', 1)) * 20,
                    appreciation=detail.get('commentaire', '')
                )
            
            # Génération du PDF professionnel
            pdf_content, context = BulletinService.generate_bulletin_professionnel(instance)
            
            # Enregistrer le PDF
            filename = f"bulletin_{eleve.last_name}_{matiere_name.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d')}.pdf"
            
            from django.core.files.base import ContentFile
            
            bulletin.file_pdf.save(filename, ContentFile(pdf_content), save=True)
            bulletin.is_signed = True
            bulletin.signature_numerique = BulletinService._generate_digital_signature(bulletin)
            bulletin.save(update_fields=['file_pdf', 'is_signed', 'signature_numerique'])
            
            logger.success(f"[BulletinAuto] ✓ Bulletin généré: {filename}")
            
        except Exception as e:
            logger.error(f"[BulletinAuto] Erreur critique: {e}", exc_info=True)
            # Ne pas lever l'exception pour ne pas bloquer la transaction Resultat


class AntiCheatLog(models.Model):
    class TypeEvent(models.TextChoices):
        TAB_CHANGE = 'tab_change', _('Changement d\'onglet')
        FULLSCREEN_EXIT = 'fullscreen_exit', _('Sortie plein écran')
        CAMERA_OFF = 'camera_off', _('Caméra désactivée')
        MULTIPLE_FACES = 'multiple_faces', _('Plusieurs visages détectés')
        COPY_PASTE = 'copy_paste', _('Copier/Coller')
        RIGHT_CLICK = 'right_click', _('Clic droit')
        SUSPICIOUS_MOVEMENT = 'suspicious_movement', _('Mouvement suspect')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(CompositionSession, on_delete=models.CASCADE, related_name='anti_cheat_logs')
    type_event = models.CharField(_('type d\'événement'), max_length=30, choices=TypeEvent.choices)
    description = models.TextField(_('description'), blank=True)
    screenshot = models.ImageField(_('capture d\'écran'), upload_to='cheat_screenshots/%Y/%m/', blank=True, null=True)
    timestamp = models.DateTimeField(_('horodatage'), default=timezone.now)

    class Meta:
        verbose_name = _('log anti-triche')
        verbose_name_plural = _('logs anti-triche')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_type_event_display()} - {self.session.eleve.full_name}"

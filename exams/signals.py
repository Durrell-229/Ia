from django.db.models.signals import post_save
from django.dispatch import receiver
from exams.models import Exam
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Exam)
def auto_generate_qcm(sender, instance, created, **kwargs):
    """
    Signal pour auto-générer un QCM lorsqu'un examen est créé.
    Désactivé par défaut pour éviter les erreurs sans IA configurée.
    """
    if created:
        try:
            from ai_engine.orchestrator import SmartOrchestrator
            from qcm.models import QCMExam
            
            orchestrator = SmartOrchestrator()
            # Génération automatique du contenu QCM via l'IA
            qcm_questions = orchestrator.generate_qcm_questions(
                topic=instance.titre, 
                grade=str(instance.classe) if instance.classe else "Général"
            )
            
            # Création automatique du QCM en base
            QCMExam.objects.create(
                exam=instance,
            )
            logger.info(f"QCM auto-généré pour l'examen: {instance.titre}")
        except Exception as e:
            # Ne pas bloquer la création d'examen si l'IA échoue
            logger.warning(f"Impossible de générer automatiquement le QCM pour '{instance.titre}': {e}")

import logging
from correction.models import CorrectionCopie, StatutCorrection

logger = logging.getLogger(__name__)


def process_ai_correction(correction_id, model_answer_path, student_pages_paths, instructions=""):
    """Correction IA SYNCHRONE via le service dédié."""
    try:
        correction = CorrectionCopie.objects.get(id=correction_id)
    except CorrectionCopie.DoesNotExist:
        logger.error(f"CorrectionCopie {correction_id} introuvable.")
        return
    
    try:
        from ai_engine.services import ai_service, extract_text_from_file
        
        # Extraire le texte du corrigé type
        corrige_text = extract_text_from_file(model_answer_path) if model_answer_path else ""
        
        # Extraire le texte des copies de l'élève
        copie_text = ""
        for path in student_pages_paths:
            copie_text += extract_text_from_file(path) + "\n"
        
        # Appel au service IA
        exam_info = {
            'titre': correction.exam.titre if correction.exam else 'Examen',
            'note_maximale': 20
        }
        result = ai_service.correct_copy(corrige_text, copie_text, exam_info)
        
        if "error" not in result:
            correction.note_ia = result.get('note', 0)
            correction.json_resultat = result
            correction.status = StatutCorrection.VALIDATION_ENSEIGNANT
            correction.save()
            logger.info(f"Correction IA terminée pour {correction_id}")
        else:
            logger.error(f"Erreur IA pour correction {correction_id}: {result.get('error')}")
    except Exception as e:
        logger.error(f"Erreur lors de la correction IA {correction_id}: {e}")

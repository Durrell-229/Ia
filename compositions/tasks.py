"""
Tâches de correction IA SYNCHRONES (SANS Celery)
Pour exécution immédiate dans les vues Django
"""
import logging
from django.shortcuts import get_object_or_404
from .models import CompositionSession, Resultat
from ai_engine.multi_ai import multi_ai
from ai_engine.services import extract_text_from_file
from io import BytesIO
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.core.files.base import ContentFile
from decimal import Decimal
from django.utils import timezone

logger = logging.getLogger(__name__)


def process_ia_correction_sync(session_id):
    """
    Correction IA SYNCHRONE pour composition - SANS Celery
    
    Appelé directement dans la vue submit_paper_view
    Blocant mais immédiat (idéal pour petits volumes)
    
    Args:
        session_id: UUID de la session de composition
        
    Returns:
        dict: Résultat de la correction avec note, mention, feedback
    """
    try:
        logger.info(f"[IA_SYNC] Démarrage correction synchrone session {session_id}")
        
        session = CompositionSession.objects.get(id=session_id)
        
        # Vérifier si déjà corrigé
        if hasattr(session, 'resultat'):
            logger.warning(f"[IA_SYNC] Session {session_id} déjà corrigée")
            return {'status': 'already_corrected'}
        
        exam = session.exam
        
        # 1. Récupérer le texte du corrigé type
        corrige_file = exam.files.filter(type_fichier='corrige_type').first()
        corrige_text = ""
        if corrige_file:
            corrige_text = extract_text_from_file(corrige_file.fichier.path)
        
        # 2. Récupérer le texte de la copie de l'élève
        copie_text = ""
        
        # Fichiers uploadés (images de copies avec OCR)
        submission_files = session.submission_files.all()
        if submission_files.exists():
            for sub in submission_files:
                copied_text = extract_text_from_file(sub.fichier.path)
                copie_text += f"\n{copied_text}"
        
        # Réponses texte directes
        answers = session.answers.all()
        if answers.exists():
            for answer in answers:
                copie_text += f"\nQuestion {answer.question_number}: {answer.content}\n"
        
        if not copie_text.strip():
            logger.error(f"[IA_SYNC] Aucun texte trouvé pour la session {session_id}")
            return {'status': 'no_content', 'error': 'Aucune copie détectée'}
        
        # 3. Appel au service IA SYNCHRONE
        exam_info = {
            'titre': exam.titre,
            'note_maximale': float(exam.note_maximale),
            'matiere': getattr(exam, 'matiere', ''),
        }
        
        # Utiliser l'orchestrateur pour fallback automatique entre providers
        from ai_engine.orchestrator import SmartOrchestrator
        orchestrator = SmartOrchestrator()
        
        # Si fichier image, utiliser correction vision
        if submission_files.exists():
            # Extraction base64 pour API vision (si nécessaire)
            logger.info(f"[IA_SYNC] Correction visuelle via orchestrateur")
            
            # Pour l'instant, fallback sur correction texte
            correction_data = orchestrator.correct_copy_text(
                student_text=copie_text[:5000],
                correction_type=corrige_text[:3000],
                exam_info=exam_info
            )
        else:
            # Correction texte standard
            correction_data = orchestrator.correct_copy_text(
                student_text=copie_text[:5000],
                correction_type=corrige_text[:3000],
                exam_info=exam_info
            )
        
        # 4. Parser la réponse JSON de l'IA
        import json
        try:
            if isinstance(correction_data, str):
                clean_json = correction_data.strip()
                if '```json' in clean_json:
                    clean_json = clean_json.split('```json')[1].split('```')[0].strip()
                elif '```' in clean_json:
                    clean_json = clean_json.split('```')[1].split('```')[0].strip()
                
                correction_result = json.loads(clean_json)
            else:
                correction_result = correction_data
        except Exception as e:
            logger.error(f"[IA_SYNC] Erreur parsing JSON IA: {e}")
            correction_result = {
                'note': 0,
                'appreciation': 'Erreur de traitement IA',
                'details': [],
                'points_forts_global': '',
                'axes_amelioration': 'Veuillez réessayer'
            }
        
        # 5. Calculer mention
        note = float(correction_result.get('note', 0))
        mention = _calculate_mention(note)
        
        # 6. Créer objet Resultat
        resultat = Resultat.objects.create(
            session=session,
            note=note,
            note_sur=Decimal(str(exam_info['note_maximale'])),
            mention=mention,
            appreciation=correction_result.get('appreciation', correction_result.get('remediation', '')),
            details_correction=correction_result,
            corrige_par_ia=True,
            corrige_at=timezone.now(),
            created_at=timezone.now()
        )
        
        logger.success(f"[IA_SYNC] ✓ Correction terminée: Note {note}/{exam_info['note_maximale']}")
        
        # Le signal post_save de Resultat déclenchera automatiquement la génération du bulletin PDF
        # via trigger_bulletin_generation()
        
        return {
            'status': 'success',
            'resultat_id': str(resultat.id),
            'note': note,
            'mention': mention,
            'appreciation': correction_result.get('appreciation', ''),
        }
        
    except Exception as e:
        logger.error(f"[IA_SYNC] Erreur critique correction session {session_id}: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


def calculate_leaderboard_sync(user_id):
    """
    Calcul leaderboard SYNCHRONE pour un utilisateur
    Appelé après chaque action gamification
    """
    from django.contrib.auth.models import User as DjangoUser
    from gamification.models import GlobalLeaderboard, XPAction
    
    user = DjangoUser.objects.get(id=user_id)
    
    # Calcul XP total
    xp_total = sum(action.points_gaines for action in XPAction.objects.filter(user=user))
    
    # Niveau basé sur XP
    niveau = max(1, xp_total // 1000 + 1)
    
    # Statistiques examens
    compositions = user.composition_sessions.filter(resultat__isnull=False)
    nb_compositions = compositions.count()
    
    scores = [float(r.note) for r in compositions.values_list('resultat__note', flat=True)]
    moyenne_generale = sum(scores) / len(scores) if scores else 0
    
    excellent_notes = sum(1 for score in scores if score >= 16)
    
    # Streak actuel
    try:
        from gamification.models import StreakRecord
        streak = user.streak
        current_streak = streak.current_streak
    except:
        current_streak = 0
    
    # Badges count
    badges_count = user.user_badges.count()
    
    # Trouver ou créer entry leaderboard
    now = timezone.now().date()
    entry, created = GlobalLeaderboard.objects.update_or_create(
        user=user,
        periode='all_time',
        date_periode=now,
        defaults={
            'score_total': xp_total,
            'points_xp': xp_total,
            'niveau': niveau,
            'nb_compositions': nb_compositions,
            'moyenne_generale': moyenne_generale,
            'streak_jours': current_streak,
            'badges_obtenus': badges_count,
        }
    )
    
    return {
        'status': 'success',
        'user_id': user_id,
        'xp_total': xp_total,
        'niveau': niveau,
        'nouveau_score': entry.score_total,
    }


# ===========================================================================
# Fonctions utilitaires
# ===========================================================================

def _calculate_mention(note: float) -> str:
    """Détermine la mention académique basée sur la note"""
    if note >= 16:
        return 'excellent'
    elif note >= 14:
        return 'tres_bien'
    elif note >= 12:
        return 'bien'
    elif note >= 10:
        return 'assez_bien'
    elif note >= 8:
        return 'passable'
    else:
        return 'insuffisant'

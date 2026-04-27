import logging
from django.utils import timezone
from itertools import combinations

from .models import PlagiarismCheck, PlagiarismPair, PlagiarismReport
from compositions.models import CompositionSession, StudentAnswer

logger = logging.getLogger(__name__)


def run_plagiarism_check(check_id: str):
    """Détection de plagiat SYNCHRONE."""
    try:
        check = PlagiarismCheck.objects.select_related('exam').get(id=check_id)
        check.statut = PlagiarismCheck.Statut.EN_COURS
        check.save()

        sessions = list(CompositionSession.objects.filter(
            exam=check.exam,
            statut__in=[CompositionSession.Statut.SOUMIS, CompositionSession.Statut.CORRIGE]
        ).select_related('eleve'))

        seuil = float(check.seuil_similarite)
        nb_paires = 0
        nb_suspectes = 0
        rapport = {'paires_suspectes': [], 'stats_globales': {}}

        for s1, s2 in combinations(sessions, 2):
            answers1 = StudentAnswer.objects.filter(session=s1).order_by('question_number')
            answers2 = StudentAnswer.objects.filter(session=s2).order_by('question_number')
            text1 = "\n".join([a.content for a in answers1])
            text2 = "\n".join([a.content for a in answers2])
            if not text1 or not text2:
                continue

            similarite = PlagiarismPair.compute_similarity(text1, text2)
            phrases_communes = PlagiarismPair.find_common_phrases(text1, text2)

            sim_par_q = {}
            for a1 in answers1:
                a2 = answers2.filter(question_number=a1.question_number).first()
                if a2:
                    sim_par_q[str(a1.question_number)] = PlagiarismPair.compute_similarity(a1.content, a2.content)

            if similarite >= 80:
                niveau = 'critique'
            elif similarite >= 60:
                niveau = 'eleve'
            elif similarite >= 30:
                niveau = 'modere'
            else:
                niveau = 'faible'

            PlagiarismPair.objects.create(
                verification=check, session_1=s1, session_2=s2,
                similarite_globale=similarite,
                similarite_par_question=sim_par_q,
                niveau_suspection=niveau,
                phrases_communes=phrases_communes,
            )
            nb_paires += 1
            if similarite >= seuil:
                nb_suspectes += 1
                rapport['paires_suspectes'].append({
                    'eleve_1': s1.eleve.full_name,
                    'eleve_2': s2.eleve.full_name,
                    'similarite': float(similarite),
                    'niveau': niveau,
                })

        rapport['stats_globales'] = {
            'total_paires': nb_paires,
            'paires_suspectes': nb_suspectes,
            'pourcentage_suspect': round(nb_suspectes / max(nb_paires, 1) * 100, 2),
        }
        check.statut = PlagiarismCheck.Statut.TERMINE
        check.nb_paires_analysees = nb_paires
        check.nb_paires_suspectes = nb_suspectes
        check.rapport_global = rapport
        check.completed_at = timezone.now()
        check.save()

        recs = []
        if nb_suspectes > 0:
            recs.append(f"{nb_suspectes} paire(s) suspecte(s) sur {nb_paires} analysées.")
            for p in rapport['paires_suspectes']:
                if p['niveau'] == 'critique':
                    recs.append(f"ALERTE: {p['eleve_1']} / {p['eleve_2']} - {p['similarite']}%")
        PlagiarismReport.objects.create(
            verification=check,
            resume=f"Analyse de {nb_paires} paires. {nb_suspectes} suspectes.",
            recommendations="\n".join(recs) if recs else "Aucun plagiat détecté.",
        )
        return {"status": "success", "paires": nb_paires, "suspectes": nb_suspectes}
    except Exception as exc:
        PlagiarismCheck.objects.filter(id=check_id).update(statut=PlagiarismCheck.Statut.ERREUR)
        logger.error(f"Erreur détection plagiat {check_id}: {exc}")
        return {"status": "error", "error": str(exc)}

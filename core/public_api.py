from ninja import Router, Schema
from typing import List, Optional
from django.http import HttpRequest

from accounts.models import User
from compositions.models import Resultat
from exams.models import Exam
from certifications.models import Certificate
from gamification.models import GlobalLeaderboard

router = Router(tags=["API Publique"])


class PublicUserOut(Schema):
    full_name: str
    country: str
    niveau: Optional[str]
    matricule: Optional[str]


class PublicLeaderboardOut(Schema):
    rang: int
    nom: str
    pays: str
    score: float
    niveau: int
    moyenne: float


class PublicCertificateOut(Schema):
    code: str
    titre: str
    eleve: str
    type: str
    date: str
    institution: str
    statut: str


class PublicStatsOut(Schema):
    total_utilisateurs: int
    total_examens: int
    total_compositions: int
    total_certificats: int
    pays_représentés: int


class PublicExamOut(Schema):
    titre: str
    matiere: Optional[str]
    type: str
    date_debut: Optional[str]
    note_maximale: float


@router.get("/stats", response=PublicStatsOut)
def public_stats(request: HttpRequest):
    return {
        "total_utilisateurs": User.objects.count(),
        "total_examens": Exam.objects.count(),
        "total_compositions": Resultat.objects.count(),
        "total_certificats": Certificate.objects.count(),
        "pays_représentés": User.objects.values('country').distinct().count(),
    }


@router.get("/leaderboard", response=List[PublicLeaderboardOut])
def public_leaderboard(request: HttpRequest, limit: int = 50):
    entries = GlobalLeaderboard.objects.filter(periode='all_time').select_related('user')[:limit]
    return [{
        "rang": e.rang_mondial,
        "nom": e.user.full_name,
        "pays": e.pays,
        "score": float(e.score_total),
        "niveau": e.niveau,
        "moyenne": float(e.moyenne),
    } for e in entries]


@router.get("/verify-certificate/{code}", response={200: PublicCertificateOut, 404: dict})
def verify_certificate(request: HttpRequest, code: str):
    try:
        cert = Certificate.objects.select_related('eleve').get(code_verification=code)
        return 200, {
            "code": cert.code_verification,
            "titre": cert.titre,
            "eleve": cert.eleve.full_name,
            "type": cert.get_type_certificat_display(),
            "date": cert.date_delivrance.strftime('%d/%m/%Y'),
            "institution": cert.institution,
            "statut": cert.get_statut_display(),
        }
    except Certificate.DoesNotExist:
        return 404, {"error": "Certificat introuvable"}


@router.get("/public-exams", response=List[PublicExamOut])
def public_exams(request: HttpRequest):
    exams = Exam.objects.filter(est_public=True, statut='publie').select_related('matiere')[:20]
    return [{
        "titre": e.titre,
        "matiere": e.matiere.nom if e.matiere else None,
        "type": e.get_type_exam_display(),
        "date_debut": e.date_debut.isoformat() if e.date_debut else None,
        "note_maximale": float(e.note_maximale),
    } for e in exams]

from typing import List, Optional
from django.http import HttpRequest
from ninja import Router, Schema, File
from ninja.files import UploadedFile
from django.shortcuts import get_object_or_404
from django.utils import timezone
import segno
from django.core.files.base import ContentFile
import io

from .models import CompositionSession, StudentAnswer, StudentSubmissionFile, Resultat, AntiCheatLog
from exams.models import Exam, ExamAssignment

router = Router()


class SessionOut(Schema):
    id: str
    exam_id: str
    exam_titre: str
    mode: str
    statut: str
    started_at: Optional[str]
    submitted_at: Optional[str]
    time_spent_seconds: int
    qr_code_url: Optional[str]


class StartSessionSchema(Schema):
    mode: str = 'en_ligne'


class AnswerIn(Schema):
    question_number: int
    content: str


class CheatEventSchema(Schema):
    type_event: str
    description: Optional[str] = None


class MessageOut(Schema):
    message: str
    success: bool = True


class ErrorOut(Schema):
    error: str
    success: bool = False


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@router.get("/sessions", response=List[SessionOut])
def list_sessions(request: HttpRequest):
    if not request.user.is_authenticated:
        return []
    sessions = CompositionSession.objects.filter(eleve=request.user).select_related('exam')
    return [{
        "id": str(s.id),
        "exam_id": str(s.exam.id),
        "exam_titre": s.exam.titre,
        "mode": s.mode,
        "statut": s.statut,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
        "time_spent_seconds": s.time_spent_seconds,
        "qr_code_url": request.build_absolute_uri(s.qr_code.url) if s.qr_code else None,
    } for s in sessions]


@router.post("/start/{exam_id}", response={200: SessionOut, 400: ErrorOut})
def start_session(request: HttpRequest, exam_id: str, payload: StartSessionSchema):
    exam = get_object_or_404(Exam, id=exam_id)

    # Vérifier que l'élève est assigné
    if request.user.role == 'eleve':
        assigned = ExamAssignment.objects.filter(
            exam=exam,
            eleve=request.user
        ).exists() or ExamAssignment.objects.filter(
            exam=exam,
            classe__isnull=False
        ).exists()
        if not assigned and not exam.est_public:
            return 400, {"error": "Vous n'êtes pas assigné à cette épreuve.", "success": False}

    session, created = CompositionSession.objects.get_or_create(
        exam=exam,
        eleve=request.user,
        defaults={
            'mode': payload.mode,
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:512],
        }
    )

    if created or session.statut == CompositionSession.Statut.EN_ATTENTE:
        session.start()

    if payload.mode == 'sur_papier' and not session.qr_code:
        token = f"ACAD-{session.id.hex[:8]}"
        session.qr_token = token
        qr = segno.make(token)
        buffer = io.BytesIO()
        qr.save(buffer, kind='png', scale=10)
        session.qr_code.save(f'qr_{session.id}.png', ContentFile(buffer.getvalue()), save=True)

    return 200, {
        "id": str(session.id),
        "exam_id": str(exam.id),
        "exam_titre": exam.titre,
        "mode": session.mode,
        "statut": session.statut,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "submitted_at": session.submitted_at.isoformat() if session.submitted_at else None,
        "time_spent_seconds": session.time_spent_seconds,
        "qr_code_url": request.build_absolute_uri(session.qr_code.url) if session.qr_code else None,
    }


@router.post("/answer/{session_id}", response={200: MessageOut, 400: ErrorOut})
def submit_answer(request: HttpRequest, session_id: str, payload: AnswerIn):
    session = get_object_or_404(CompositionSession, id=session_id, eleve=request.user)
    if session.statut != CompositionSession.Statut.EN_COURS:
        return 400, {"error": "La session n'est pas en cours.", "success": False}

    StudentAnswer.objects.update_or_create(
        session=session,
        question_number=payload.question_number,
        defaults={'content': payload.content}
    )
    return 200, {"message": "Réponse enregistrée.", "success": True}


@router.post("/upload-page/{session_id}", response={200: MessageOut, 400: ErrorOut})
def upload_page(request: HttpRequest, session_id: str, page_number: int, fichier: UploadedFile = File(...)):
    session = get_object_or_404(CompositionSession, id=session_id, eleve=request.user)
    if session.statut != CompositionSession.Statut.EN_COURS and session.statut != CompositionSession.Statut.SOUMIS:
        return 400, {"error": "Impossible d'uploader à ce stade.", "success": False}

    StudentSubmissionFile.objects.create(
        session=session,
        fichier=fichier,
        page_number=page_number
    )
    return 200, {"message": "Page uploadée avec succès.", "success": True}


@router.post("/submit/{session_id}", response={200: MessageOut, 400: ErrorOut})
def submit_session(request: HttpRequest, session_id: str):
    session = get_object_or_404(CompositionSession, id=session_id, eleve=request.user)
    if session.statut != CompositionSession.Statut.EN_COURS:
        return 400, {"error": "La session n'est pas en cours.", "success": False}

    session.submit()
    # Créer le résultat vide en attente de correction
    Resultat.objects.get_or_create(
        session=session,
        defaults={'note': 0, 'note_sur': session.exam.note_maximale}
    )
    return 200, {"message": "Composition soumise avec succès. En attente de correction.", "success": True}


@router.post("/cheat-event/{session_id}", response={200: MessageOut, 400: ErrorOut})
def log_cheat_event(request: HttpRequest, session_id: str, payload: CheatEventSchema):
    session = get_object_or_404(CompositionSession, id=session_id, eleve=request.user)
    log = AntiCheatLog.objects.create(
        session=session,
        type_event=payload.type_event,
        description=payload.description or '',
    )
    session.cheat_count += 1
    session.cheat_logs.append({
        'type': payload.type_event,
        'time': timezone.now().isoformat(),
        'description': payload.description,
    })

    if session.cheat_count >= 3:
        session.statut = CompositionSession.Statut.EXCLU
        session.save()
        return 200, {"message": "ALERTE : Vous avez été exclu pour triche.", "success": False}

    session.save()
    return 200, {"message": f"Événement enregistré. Attention ({session.cheat_count}/3).", "success": True}


@router.get("/resultat/{session_id}")
def get_resultat(request: HttpRequest, session_id: str):
    session = get_object_or_404(CompositionSession, id=session_id, eleve=request.user)
    resultat = getattr(session, 'resultat', None)
    if not resultat:
        return {"error": "Pas encore de résultat."}
    return {
        "note": float(resultat.note),
        "note_sur": float(resultat.note_sur),
        "mention": resultat.mention,
        "appreciation": resultat.appreciation,
        "classement": resultat.classement,
        "total_participants": resultat.total_participants,
        "details_correction": resultat.details_correction,
        "bulletin_url": request.build_absolute_uri(resultat.bulletin_pdf.url) if resultat.bulletin_pdf else None,
    }

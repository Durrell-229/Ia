from ninja import Router, Schema, File, Form
from ninja.files import UploadedFile
from compositions.models import CompositionSession, StudentSubmissionFile, StudentAnswer
from exams.models import Exam
from django.shortcuts import get_object_or_404
from django.utils import timezone
import uuid
from ai_engine.tasks import process_ai_correction

router = Router()

class AnswerSchema(Schema):
    question_number: int
    content: str

class CheatSchema(Schema):
    message: str

@router.post("/{exam_id}/start")
def start_composition(request, exam_id: uuid.UUID):
    exam = get_object_or_404(Exam, id=exam_id)
    session, created = CompositionSession.objects.get_or_create(
        exam=exam,
        eleve=request.user,
        defaults={'statut': 'en_cours', 'started_at': timezone.now()}
    )
    
    if not created and session.statut == 'soumis':
        return {"error": "Cet examen a déjà été soumis."}, 400
    
    session.statut = 'en_cours'
    if not session.started_at:
        session.started_at = timezone.now()
    session.save()
    return {"session_id": str(session.id), "status": session.statut}

@router.post("/save-answer/{session_id}")
def save_answer(request, session_id: uuid.UUID, data: AnswerSchema):
    session = get_object_or_404(CompositionSession, id=session_id)
    if session.statut != 'en_cours':
        return {"error": "La session n'est plus active."}, 403
        
    answer, created = StudentAnswer.objects.update_or_create(
        session=session,
        question_number=data.question_number,
        defaults={'content': data.content}
    )
    return {"status": "success", "saved_at": timezone.now().isoformat()}

@router.post("/upload-page/{session_id}")
def upload_page(
    request, 
    session_id: uuid.UUID, 
    file: UploadedFile = File(...), 
    page_number: int = Form(1)
):
    """
    Upload REEL et VERIFIE pour les copies papier.
    """
    session = get_object_or_404(CompositionSession, id=session_id)
    
    # Sécurité : Validation du type MIME
    if not file.content_type.startswith('image/'):
        return {"error": "Type de fichier non autorisé. Images uniquement."}, 400

    try:
        submission_file = StudentSubmissionFile.objects.create(
            session=session,
            fichier=file,
            page_number=page_number
        )
        return {
            "message": f"Page {page_number} enregistrée", 
            "id": str(submission_file.id),
            "filename": file.name
        }
    except Exception as e:
        return {"error": f"Erreur lors de l'enregistrement : {str(e)}"}, 500

@router.post("/submit/{session_id}")
def submit_composition(request, session_id: uuid.UUID):
    session = get_object_or_404(CompositionSession, id=session_id)
    if session.statut == 'soumis':
        return {"message": "Déjà soumis"}
        
    session.submit()
    
    # Correction IA synchrone
    process_ai_correction(str(session.id))
    
    return {"message": "Examen soumis. Correction IA effectuée.", "status": session.statut}

@router.post("/report-cheat/{session_id}")
def report_cheat(request, session_id: uuid.UUID, data: CheatSchema):
    session = get_object_or_404(CompositionSession, id=session_id)
    session.cheat_count += 1
    
    new_log = {
        "timestamp": timezone.now().isoformat(),
        "reason": data.message,
        "count": session.cheat_count
    }
    
    if not isinstance(session.cheat_logs, list):
        session.cheat_logs = []
    
    session.cheat_logs.append(new_log)
    
    if session.cheat_count >= 3:
        session.statut = 'exclu'
        
    session.save()
    return {"cheat_count": session.cheat_count, "status": session.statut}

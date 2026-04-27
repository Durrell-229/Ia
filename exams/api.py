from typing import List, Optional
from django.http import HttpRequest
from ninja import Router, Schema, File
from ninja.files import UploadedFile
from ninja.pagination import paginate
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Exam, ExamFile, ExamAssignment
from core.models import Matiere, Classe

router = Router()


class ExamOut(Schema):
    id: str
    titre: str
    description: str
    type_exam: str
    type_exam_display: str
    matiere_id: Optional[str]
    classe_id: Optional[str]
    duree_minutes: int
    date_debut: Optional[str]
    date_fin: Optional[str]
    note_maximale: float
    coefficient: float
    statut: str
    instructions: str
    anti_cheat_active: bool
    camera_required: bool
    fullscreen_required: bool


class ExamCreateSchema(Schema):
    titre: str
    description: Optional[str] = None
    type_exam: str = 'composition'
    matiere_id: Optional[str] = None
    classe_id: Optional[str] = None
    duree_minutes: int = 60
    date_debut: str
    date_fin: str
    note_maximale: float = 20.0
    coefficient: float = 1.0
    instructions: Optional[str] = None
    anti_cheat_active: bool = True
    camera_required: bool = True
    fullscreen_required: bool = True


class MessageOut(Schema):
    message: str
    success: bool = True


class ErrorOut(Schema):
    error: str
    success: bool = False


@router.get("/list", response=List[ExamOut])
@paginate
def list_exams(request: HttpRequest, statut: Optional[str] = None, search: Optional[str] = None):
    qs = Exam.objects.all().select_related('matiere', 'classe')
    if request.user.role == 'professeur':
        qs = qs.filter(createur=request.user)
    elif request.user.role == 'eleve':
        qs = qs.filter(assignments__eleve=request.user) | qs.filter(assignments__classe__isnull=False)
    if statut:
        qs = qs.filter(statut=statut)
    if search:
        qs = qs.filter(titre__icontains=search)
    return qs


@router.get("/{exam_id}", response={200: ExamOut, 404: ErrorOut})
def get_exam(request: HttpRequest, exam_id: str):
    exam = get_object_or_404(Exam, id=exam_id)
    return 200, {
        "id": str(exam.id),
        "titre": exam.titre,
        "description": exam.description,
        "type_exam": exam.type_exam,
        "type_exam_display": exam.get_type_exam_display(),
        "matiere_id": str(exam.matiere.id) if exam.matiere else None,
        "classe_id": str(exam.classe.id) if exam.classe else None,
        "duree_minutes": exam.duree_minutes,
        "date_debut": exam.date_debut.isoformat() if exam.date_debut else None,
        "date_fin": exam.date_fin.isoformat() if exam.date_fin else None,
        "note_maximale": float(exam.note_maximale),
        "coefficient": float(exam.coefficient),
        "statut": exam.statut,
        "instructions": exam.instructions,
        "anti_cheat_active": exam.anti_cheat_active,
        "camera_required": exam.camera_required,
        "fullscreen_required": exam.fullscreen_required,
    }


@router.post("/create", response={200: MessageOut, 400: ErrorOut})
def create_exam(request: HttpRequest, payload: ExamCreateSchema):
    if request.user.role not in ['admin', 'conseiller', 'professeur']:
        return 400, {"error": "Permission refusée.", "success": False}

    matiere = None
    if payload.matiere_id:
        matiere = get_object_or_404(Matiere, id=payload.matiere_id)
    classe = None
    if payload.classe_id:
        classe = get_object_or_404(Classe, id=payload.classe_id)

    exam = Exam.objects.create(
        titre=payload.titre,
        description=payload.description or '',
        type_exam=payload.type_exam,
        matiere=matiere,
        classe=classe,
        createur=request.user,
        duree_minutes=payload.duree_minutes,
        date_debut=payload.date_debut,
        date_fin=payload.date_fin,
        note_maximale=payload.note_maximale,
        coefficient=payload.coefficient,
        instructions=payload.instructions or '',
        anti_cheat_active=payload.anti_cheat_active,
        camera_required=payload.camera_required,
        fullscreen_required=payload.fullscreen_required,
    )
    return 200, {"message": f"Épreuve '{exam.titre}' créée avec succès.", "success": True}


@router.post("/{exam_id}/upload-file", response={200: MessageOut, 400: ErrorOut})
def upload_exam_file(request: HttpRequest, exam_id: str, type_fichier: str, fichier: UploadedFile = File(...)):
    exam = get_object_or_404(Exam, id=exam_id)
    if request.user != exam.createur and request.user.role != 'admin':
        return 400, {"error": "Permission refusée.", "success": False}

    ExamFile.objects.create(
        exam=exam,
        type_fichier=type_fichier,
        fichier=fichier,
        nom_original=fichier.name,
    )
    return 200, {"message": "Fichier uploadé avec succès.", "success": True}


@router.post("/{exam_id}/assign", response={200: MessageOut, 400: ErrorOut})
def assign_exam(request: HttpRequest, exam_id: str, eleve_ids: Optional[List[str]] = None, classe_ids: Optional[List[str]] = None):
    exam = get_object_or_404(Exam, id=exam_id)
    if request.user.role not in ['admin', 'conseiller', 'professeur']:
        return 400, {"error": "Permission refusée.", "success": False}

    created = 0
    if eleve_ids:
        from accounts.models import User
        for eid in eleve_ids:
            eleve = User.objects.filter(id=eid, role='eleve').first()
            if eleve:
                ExamAssignment.objects.get_or_create(exam=exam, eleve=eleve, defaults={'assigned_by': request.user})
                created += 1
    if classe_ids:
        for cid in classe_ids:
            classe = Classe.objects.filter(id=cid).first()
            if classe:
                ExamAssignment.objects.get_or_create(exam=exam, classe=classe, defaults={'assigned_by': request.user})
                created += 1

    return 200, {"message": f"Épreuve assignée à {created} destination(s).", "success": True}

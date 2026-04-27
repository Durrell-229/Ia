from ninja import Router, Schema, File, Form
from ninja.files import UploadedFile
from exams.models import Exam, ExamFile
from core.models import Matiere, Classe
from django.shortcuts import get_object_or_404
from django.utils import timezone
import uuid
from typing import List

router = Router()

class ExamOut(Schema):
    id: uuid.UUID
    titre: str
    type_exam: str
    duree_minutes: int
    statut: str

@router.get("/", response=List[ExamOut])
def list_exams(request):
    return Exam.objects.all()

@router.post("/create-with-files")
def create_exam_with_files(
    request,
    titre: str = Form(...),
    matiere_id: uuid.UUID = Form(...),
    type_exam: str = Form(...),
    duree: int = Form(60),
    date_debut: str = Form(...),
    date_fin: str = Form(...),
    epreuve_file: UploadedFile = File(...),
    corrige_file: UploadedFile = File(...)
):
    """
    Endpoint de PRODUCTION pour créer une épreuve avec ses fichiers sources.
    Indispensable pour la correction IA.
    """
    matiere = get_object_or_404(Matiere, id=matiere_id)
    
    # 1. Création de l'épreuve
    exam = Exam.objects.create(
        titre=titre,
        matiere=matiere,
        type_exam=type_exam,
        duree_minutes=duree,
        date_debut=date_debut,
        date_fin=date_fin,
        createur=request.user,
        statut='publie'
    )

    # 2. Upload de l'épreuve (PDF/Word)
    ExamFile.objects.create(
        exam=exam,
        type_fichier='epreuve',
        fichier=epreuve_file,
        nom_original=epreuve_file.name
    )

    # 3. Upload du CORRIGÉ TYPE (Source de vérité pour l'IA)
    ExamFile.objects.create(
        exam=exam,
        type_fichier='corrige_type',
        fichier=corrige_file,
        nom_original=corrige_file.name
    )

    return {
        "status": "success",
        "message": "Examen créé avec succès. L'IA est prête pour la correction.",
        "exam_id": str(exam.id)
    }

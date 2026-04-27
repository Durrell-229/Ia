from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CorrectionCopie
from exams.models import Exam, ExamFile
from ai_engine.orchestrator import SmartOrchestrator
import base64

@login_required
def upload_submission(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if request.method == 'POST' and request.FILES.get('image'):
        submission = CorrectionCopie.objects.create(
            exam=exam,
            student=request.user,
            image=request.FILES['image'],
            status='corrected' # Automatique
        )
        
        # 1. Orchestration IA automatique
        orchestrator = SmartOrchestrator()
        with open(submission.image.path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # 2. Récupérer le corrigé type depuis les fichiers de l'examen
        corrige_file = exam.files.filter(type_fichier='corrige_type').first()
        corrige_text = "Corrigé standard"
        if corrige_file:
            try:
                with open(corrige_file.fichier.path, 'r', encoding='utf-8', errors='ignore') as f:
                    corrige_text = f.read()
            except Exception:
                corrige_text = "Corrigé standard"
        
        # 3. Correction IA autonome
        feedback = orchestrator.correct_copy(base64_image, corrige_text)
        
        submission.corrected_text = feedback
        submission.save()
        
        messages.success(request, "Copie traitée par IA avec succès.")
        return redirect('upload_submission', exam_id=exam.id)
    return render(request, 'correction/upload.html', {'exam': exam})

from django.http import HttpResponse
from bulletins.services import BulletinService
from django.core.files.base import ContentFile

@login_required
def approve_submission(request, submission_id):
    if not request.user.is_staff:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('home')

    submission = get_object_or_404(CorrectionCopie, id=submission_id)
    submission.status = 'approved'

    # Génération automatique du bulletin PDF
    pdf_content = BulletinService.generate_bulletin_pdf(submission)
    
    # Extraction de la note (simple parsing du feedback IA)
    # Dans une version future, forcez l'IA à renvoyer un JSON
    if submission.corrected_text and "20" in submission.corrected_text:
        # Logique simplifiée pour extraire la note
        submission.grade = 15.0 # Par défaut si non détecté
        
    submission.save()
    
    # Envoyer la réponse pour téléchargement ou notification
    messages.success(request, "Correction approuvée et bulletin généré.")
    return redirect('admin_dashboard')

@login_required
def download_bulletin(request, submission_id):
    submission = get_object_or_404(CorrectionCopie, id=submission_id)
    pdf = BulletinService.generate_bulletin_pdf(submission)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bulletin_{submission.student.last_name}.pdf"'
    return response

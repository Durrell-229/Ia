from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Exam, ExamFile
from core.models import Matiere, Classe

from core.constants import CLASSE_CHOICES, MATIERE_CHOICES

@login_required
def exam_list_view(request):
    exams = Exam.objects.all()
    return render(request, 'exams/exam_list.html', {
        'exams': exams,
        'matiere_choices': MATIERE_CHOICES,
        'classe_choices': CLASSE_CHOICES
    })

@login_required
def exam_create_view(request):
    if request.user.role not in ['professeur', 'admin']:
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        titre = request.POST.get('titre')
        matiere_id = request.POST.get('matiere')
        classe_id = request.POST.get('classe')
        duree = request.POST.get('duree') or 60  # Défaut 60 min
        date_debut_str = request.POST.get('date_debut')
        
        from django.utils import timezone
        from datetime import timedelta
        
        if date_debut_str:
            date_debut = timezone.datetime.fromisoformat(date_debut_str)
            if timezone.is_naive(date_debut):
                date_debut = timezone.make_aware(date_debut)
        else:
            date_debut = timezone.now()
            
        date_fin = date_debut + timedelta(minutes=int(duree))
        
        # Création de l'examen
        exam = Exam.objects.create(
            titre=titre,
            matiere_id=matiere_id,
            classe_id=classe_id,
            duree_minutes=int(duree),
            date_debut=date_debut,
            date_fin=date_fin,
            createur=request.user,
            statut='publie'
        )
        
        # Gestion de l'upload des fichiers
        if request.FILES.get('file_epreuve'):
            f = request.FILES.get('file_epreuve')
            ExamFile.objects.create(
                exam=exam,
                type_fichier='epreuve',
                fichier=f,
                nom_original=f.name
            )
            
        if request.FILES.get('file_corrige'):
            f = request.FILES.get('file_corrige')
            ExamFile.objects.create(
                exam=exam,
                type_fichier='corrige_type',
                fichier=f,
                nom_original=f.name
            )
            
        messages.success(request, f"L'épreuve '{titre}' a été créée avec succès.")
        return redirect('dashboard')

    return render(request, 'exams/exam_form.html', {
        'matieres': Matiere.objects.all(),
        'classes': Classe.objects.all()
    })

@login_required
def exam_detail_view(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    return render(request, 'exams/exam_detail.html', {'exam': exam})

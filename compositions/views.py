from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils import timezone
from .models import CompositionSession
from exams.models import Exam, ExamAssignment


@login_required
def composition_room_view(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if request.user.role != 'eleve':
        return HttpResponseForbidden("Seuls les élèves peuvent accéder à la salle de composition.")

    assigned = ExamAssignment.objects.filter(
        exam=exam, eleve=request.user
    ).exists() or ExamAssignment.objects.filter(
        exam=exam, classe__isnull=False
    ).exists()

    if not assigned and not exam.est_public:
        return HttpResponseForbidden("Vous n'êtes pas assigné à cette épreuve.")

    session, created = CompositionSession.objects.get_or_create(
        exam=exam,
        eleve=request.user,
        defaults={
            'mode': 'en_ligne',
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:512],
        }
    )

    if exam.is_en_cours and session.statut == CompositionSession.Statut.EN_ATTENTE:
        session.start()

    files = exam.files.filter(type_fichier='epreuve')

    return render(request, 'compositions/room.html', {
        'exam': exam,
        'session': session,
        'files': files,
        'is_active': exam.is_en_cours and session.statut == CompositionSession.Statut.EN_COURS,
    })


@login_required
def submit_paper_view(request, session_id):
    session = get_object_or_404(CompositionSession, id=session_id, eleve=request.user)
    
    if request.method == 'POST' and request.FILES.getlist('copies'):
        from .models import StudentSubmissionFile
        files = request.FILES.getlist('copies')
        
        for i, f in enumerate(files):
            StudentSubmissionFile.objects.create(
                session=session,
                fichier=f,
                page_number=i+1
            )
        
        session.submit()
        
        # Correction IA SYNCHRONE (sans Celery)
        from .tasks import process_ia_correction_sync
        result = process_ia_correction_sync(session.id)
        
        return redirect('result_detail', session_id=session.id)

    return render(request, 'compositions/submit_paper.html', {'session': session})

@login_required
def result_view(request, session_id):
    session = get_object_or_404(CompositionSession, id=session_id, eleve=request.user)
    resultat = getattr(session, 'resultat', None)
    return render(request, 'compositions/result.html', {
        'session': session,
        'resultat': resultat,
    })

@login_required
def ia_corrections_list_view(request):
    from .models import Resultat
    if request.user.role == 'eleve':
        resultats = Resultat.objects.filter(session__eleve=request.user, corrige_par_ia=True)
    elif request.user.role == 'professeur':
        resultats = Resultat.objects.filter(session__exam__createur=request.user, corrige_par_ia=True)
    else: # admin
        resultats = Resultat.objects.filter(corrige_par_ia=True)
        
    return render(request, 'compositions/ia_corrections.html', {'resultats': resultats})

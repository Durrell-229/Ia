from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from cours.models import Course
from ai_engine.orchestrator import SmartOrchestrator

@login_required
def course_list_view(request):
    courses = Course.objects.filter(is_published=True)
    return render(request, 'cours/list.html', {'courses': courses})

from core.constants import CLASSE_CHOICES, MATIERE_CHOICES

@login_required
def create_course(request):
    if not request.user.is_staff:
        messages.error(request, "Accès réservé aux professeurs.")
        return redirect('home')
    
    if request.method == 'POST':
        # Logic de création ici...
        messages.success(request, "Cours soumis pour approbation.")
        return redirect('cours:index')
        
    return render(request, 'cours/create.html', {
        'classe_choices': CLASSE_CHOICES,
        'matiere_choices': MATIERE_CHOICES
    })

@login_required
def create_qcm_view(request, course_id):
    if not request.user.is_staff: # Seuls les profs/staff peuvent générer
        messages.error(request, "Accès restreint.")
        return redirect('home')

    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        topic = request.POST.get('topic')
        matiere_nom = request.POST.get('matiere_nom')
        grade = request.POST.get('grade')
        
        orchestrator = SmartOrchestrator()
        # Passage des nouveaux champs à l'orchestrateur
        prompt_info = f"Sujet: {topic}, Matière: {matiere_nom}, Classe: {grade}"
        qcm_content = orchestrator.generate_qcm(topic, f"{matiere_nom} - {grade}")
        
        return render(request, 'cours/qcm_generated.html', {
            'qcm': qcm_content,
            'course': course
        })
        
    return render(request, 'cours/create_qcm.html', {'course': course})

@login_required
def admin_approve_course(request, course_id):
    return admin_validate_action(request, 'course', course_id)

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'cours/detail.html', {'course': course})

@login_required
def admin_validate_action(request, model_type, item_id):
    if not request.user.is_superuser:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('home')
        
    obj = None
    if model_type == 'course':
        obj = get_object_or_404(Course, id=item_id)
    # ... autres modèles
    
    if obj is None:
        messages.error(request, "Type de modèle invalide.")
        return redirect('admin_dashboard')
    
    obj.status = 'approved'
    obj.is_published = True
    obj.save()
    messages.success(request, "Approuvé avec succès.")
    return redirect('admin_dashboard')

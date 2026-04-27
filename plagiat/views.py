from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse

from .models import PlagiarismCheck, PlagiarismPair, PlagiarismReport
from .tasks import run_plagiarism_check
from exams.models import Exam


@login_required
def run_plagiarism_check_view(request, exam_id):
    if request.user.role not in ['admin', 'conseiller', 'professeur']:
        return HttpResponseForbidden()
    exam = get_object_or_404(Exam, id=exam_id)
    check = PlagiarismCheck.objects.create(exam=exam, declenche_par=request.user)
    run_plagiarism_check(str(check.id))
    return JsonResponse({'check_id': str(check.id), 'status': 'completed'})


@login_required
def plagiarism_report_view(request, check_id):
    check = get_object_or_404(PlagiarismCheck, id=check_id)
    pairs = check.pairs.select_related('session_1__eleve', 'session_2__eleve').all()
    report = getattr(check, 'report', None)
    return render(request, 'plagiat/report.html', {
        'check': check, 'pairs': pairs, 'report': report,
    })

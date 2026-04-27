from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    context = {
        'total_exams': 0,
        'avg_score': 0,
        'study_hours': 0,
        'streak': 0,
        'recent_activities': [],
    }
    return render(request, 'analytics/dashboard.html', context)

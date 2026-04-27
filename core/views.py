from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from exams.models import Exam
from notifications.models import Notification

def home_view(request):
    return render(request, 'welcome.html', {'is_home': True})

@login_required
def admin_dashboard_view(request):
    if not request.user.is_superuser:
        return redirect('home')
        
    pending_exams = Exam.objects.filter(approval_status='pending')
    notifications = Notification.objects.all()[:10]
    
    return render(request, 'admin/dashboard.html', {
        'pending_exams': pending_exams,
        'pending_count': pending_exams.count(),
        'notifications': notifications
    })

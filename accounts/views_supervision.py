from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def supervision_view(request):
    user = request.user
    users = User.objects.all()
    
    if user.role == 'admin':
        members = users
    elif user.role == 'conseiller':
        # CP voit les profs et les élèves
        members = users.filter(role__in=['professeur', 'eleve'])
    elif user.role == 'professeur':
        # Prof voit les élèves
        members = users.filter(role='eleve')
    else:
        members = User.objects.none()
        
    return render(request, 'accounts/supervision.html', {'members': members})

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from django import forms
from .models import User

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'bio', 'avatar']



def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Email ou mot de passe incorrect.")
    return render(request, 'accounts/login.html', {'is_auth_page': True})


@login_required
def dashboard_view(request):
    user = request.user
    role = user.role

    from exams.models import Exam, ExamAssignment
    from compositions.models import CompositionSession, Resultat

    now = timezone.now()
    context = {'user': user}

    # ─────────────────────────────────────────
    # DASHBOARD ÉLÈVE
    # ─────────────────────────────────────────
    if role == 'eleve':
        # Épreuves assignées : par élève OU par classe
        if user.classe:
            assigned_qs = Exam.objects.filter(
                Q(assignments__eleve=user) | Q(classe__nom=user.classe)
            ).distinct()
        else:
            assigned_qs = Exam.objects.filter(assignments__eleve=user).distinct()

        upcoming_exams = assigned_qs.filter(
            date_debut__gte=now
        ).order_by('date_debut')[:5]

        active_exams = assigned_qs.filter(
            date_debut__lte=now,
            date_fin__gte=now,
            statut='en_cours'
        )

        sessions = CompositionSession.objects.filter(
            eleve=user
        ).select_related('exam', 'exam__matiere')

        results = Resultat.objects.filter(
            session__eleve=user
        ).select_related(
            'session', 'session__exam', 'session__exam__matiere'
        ).order_by('-created_at')

        # Stats
        moyenne = results.aggregate(Avg('note'))['note__avg'] or 0
        total_minutes = sessions.aggregate(
            Sum('exam__duree_minutes')
        )['exam__duree_minutes__sum'] or 0

        # Progression sur les 3 derniers vs 3 précédents
        recent_3 = list(results.values_list('note', flat=True)[:3])
        prev_3 = list(results.values_list('note', flat=True)[3:6])
        recent_avg = sum(float(n) for n in recent_3) / len(recent_3) if recent_3 else 0
        prev_avg = sum(float(n) for n in prev_3) / len(prev_3) if prev_3 else 0
        progression = round(recent_avg - prev_avg, 1) if prev_3 else 0

        # Badges
        try:
            from gamification.models import UserBadge, StreakRecord, XPAction
            badges = UserBadge.objects.filter(user=user).select_related('badge')[:6]
            streak, _ = StreakRecord.objects.get_or_create(user=user)
            streak.update_streak()
            total_xp = XPAction.objects.filter(user=user).aggregate(
                Sum('points_gagnes')
            )['points_gagnes__sum'] or 0
        except Exception:
            badges = []
            streak = type('Streak', (), {'current_streak': 0, 'longest_streak': 0})()
            total_xp = 0

        pending_sessions = sessions.filter(statut='soumis')

        context.update({
            'assigned_exams': assigned_qs,
            'upcoming_exams': upcoming_exams,
            'active_exams': active_exams,
            'resultats': results[:10],
            'sessions': sessions,
            'moyenne': round(float(moyenne), 1),
            'total_exams': results.count(),
            'total_hours': round(total_minutes / 60, 1),
            'progression': progression,
            'pending_sessions': pending_sessions,
            'badges': badges,
            'streak': streak,
            'total_xp': total_xp,
        })
        return render(request, 'accounts/dashboard_eleve.html', context)

    # ─────────────────────────────────────────
    # DASHBOARD PROFESSEUR
    # ─────────────────────────────────────────
    elif role == 'professeur':
        my_exams = Exam.objects.filter(createur=user).select_related('matiere', 'classe')

        total_my_exams = my_exams.count()
        exams_en_cours = my_exams.filter(statut='en_cours').count()
        exams_termines = my_exams.filter(statut='termine').count()
        exams_brouillon = my_exams.filter(statut='brouillon').count()

        related_sessions = CompositionSession.objects.filter(
            exam__createur=user
        ).select_related('eleve', 'exam')

        total_compositions = related_sessions.count()
        pending_corrections = related_sessions.filter(statut='soumis').count()
        corrected_count = related_sessions.filter(statut='corrige').count()

        my_results = Resultat.objects.filter(
            session__exam__createur=user
        ).select_related('session', 'session__eleve', 'session__exam')

        avg_class_score = my_results.aggregate(Avg('note'))['note__avg'] or 0
        corrections_ia = my_results.filter(corrige_par_ia=True).count()

        recent_submissions = related_sessions.filter(
            statut='soumis'
        ).order_by('-submitted_at')[:10]

        top_students = my_results.order_by('-note')[:5]
        weak_students = my_results.filter(note__lt=10).order_by('note')[:5]
        unique_students = related_sessions.values('eleve').distinct().count()

        # Distribution notes pour graphique
        def count_range(qs, lo, hi):
            return qs.filter(note__gte=lo, note__lt=hi).count()

        passable_count = count_range(my_results, 10, 12)
        assez_bien_count = count_range(my_results, 12, 14)
        bien_count = count_range(my_results, 14, 16)
        tres_bien_count = count_range(my_results, 16, 18)
        excellent_count = my_results.filter(note__gte=18).count()

        context.update({
            'exams': my_exams.order_by('-created_at')[:20],
            'total_my_exams': total_my_exams,
            'exams_en_cours': exams_en_cours,
            'exams_termines': exams_termines,
            'exams_brouillon': exams_brouillon,
            'total_compositions': total_compositions,
            'total_eleves': unique_students,
            'pending_corrections': pending_corrections,
            'corrected_count': corrected_count,
            'corrections_ia': corrections_ia,
            'avg_class_score': round(float(avg_class_score), 1),
            'recent_submissions': recent_submissions,
            'top_students': top_students,
            'weak_students': weak_students,
            'passable_count': passable_count,
            'assez_bien_count': assez_bien_count,
            'bien_count': bien_count,
            'tres_bien_count': tres_bien_count,
            'excellent_count': excellent_count,
        })
        return render(request, 'accounts/dashboard_professeur.html', context)

    # ─────────────────────────────────────────
    # DASHBOARD CONSEILLER
    # ─────────────────────────────────────────
    elif role == 'conseiller':
        total_users = User.objects.count()
        total_profs = User.objects.filter(role='professeur').count()
        total_eleves = User.objects.filter(role='eleve').count()
        total_exams = Exam.objects.count()
        total_sessions = CompositionSession.objects.count()
        total_results = Resultat.objects.count()

        pending_approvals = Exam.objects.filter(
            approval_status='pending'
        ).select_related('createur', 'matiere', 'classe').order_by('-created_at')

        avg_global = Resultat.objects.aggregate(Avg('note'))['note__avg'] or 0
        ia_corrections = Resultat.objects.filter(corrige_par_ia=True).count()

        prof_activity = User.objects.filter(role='professeur').annotate(
            nb_exams=Count('exams_crees', distinct=True),
            nb_corrections=Count('exams_crees__sessions__resultat', distinct=True)
        ).order_by('-nb_exams')[:8]

        live_sessions = CompositionSession.objects.filter(
            statut='en_cours'
        ).select_related('eleve', 'exam')[:10]

        context.update({
            'total_users': total_users,
            'total_profs': total_profs,
            'total_eleves': total_eleves,
            'total_exams': total_exams,
            'total_sessions': total_sessions,
            'total_results': total_results,
            'pending_approvals': pending_approvals,
            'pending_count': pending_approvals.count(),
            'avg_global': round(float(avg_global), 1),
            'ia_corrections': ia_corrections,
            'prof_activity': prof_activity,
            'live_sessions': live_sessions,
        })
        return render(request, 'accounts/dashboard_conseiller.html', context)

    # ─────────────────────────────────────────
    # DASHBOARD ADMIN
    # ─────────────────────────────────────────
    elif role == 'admin':
        total_users = User.objects.count()
        total_eleves = User.objects.filter(role='eleve').count()
        total_profs = User.objects.filter(role='professeur').count()
        total_conseillers = User.objects.filter(role='conseiller').count()
        total_exams = Exam.objects.count()
        total_sessions = CompositionSession.objects.count()
        total_results = Resultat.objects.count()

        pending_approvals = Exam.objects.filter(
            approval_status='pending'
        ).select_related('createur', 'matiere').order_by('-created_at')

        avg_global = Resultat.objects.aggregate(Avg('note'))['note__avg'] or 0
        ia_corrections = Resultat.objects.filter(corrige_par_ia=True).count()
        human_corrections = Resultat.objects.filter(corrige_par_humain=True).count()

        live_sessions = CompositionSession.objects.filter(
            statut='en_cours'
        ).select_related('eleve', 'exam')

        cheat_sessions = CompositionSession.objects.filter(statut='exclu').count()
        cheat_rate = round((cheat_sessions / total_sessions * 100), 1) if total_sessions > 0 else 0

        week_ago = now - timedelta(days=7)
        new_users_week = User.objects.filter(date_joined__gte=week_ago).count()

        recent_results = Resultat.objects.select_related(
            'session', 'session__eleve', 'session__exam'
        ).order_by('-created_at')[:15]

        try:
            from notifications.models import Notification
            unread_notifs = Notification.objects.filter(is_read=False).count()
        except Exception:
            unread_notifs = 0

        context.update({
            'is_admin': True,
            'total_users': total_users,
            'total_eleves': total_eleves,
            'total_profs': total_profs,
            'total_conseillers': total_conseillers,
            'total_exams': total_exams,
            'total_sessions': total_sessions,
            'total_results': total_results,
            'pending_approvals': pending_approvals,
            'pending_count': pending_approvals.count(),
            'avg_global': round(float(avg_global), 1),
            'ia_corrections': ia_corrections,
            'human_corrections': human_corrections,
            'live_sessions': live_sessions,
            'live_count': live_sessions.count(),
            'cheat_sessions': cheat_sessions,
            'cheat_rate': cheat_rate,
            'new_users_week': new_users_week,
            'recent_results': recent_results,
            'unread_notifs': unread_notifs,
            'AI_PROVIDER': getattr(settings, 'AI_PROVIDER', 'gemini'),
        })
        return render(request, 'accounts/dashboard_admin.html', context)

    # Fallback
    return redirect('login')


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        role = request.POST.get('role', 'eleve')
        role_password = request.POST.get('role_password', '')
        phone = request.POST.get('phone', '')
        country = request.POST.get('country', 'France')
        niveau = request.POST.get('niveau', '')
        classe = request.POST.get('classe', '')

        # Vérification des rôles privilégiés
        if role in ['admin', 'conseiller', 'professeur']:
            expected = getattr(settings, f'ROLE_PASSWORD_{role.upper()}', None)
            if not expected or role_password != expected:
                messages.error(request, "Code d'accès invalide pour ce rôle.")
                return render(request, 'accounts/register.html', {'is_auth_page': True})

        if User.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé.")
        elif not email or not password:
            messages.error(request, "Email et mot de passe requis.")
        else:
            try:
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                    phone=phone,
                    country=country,
                    niveau=niveau,
                    classe=classe,
                )
                login(request, user)
                messages.success(request, f"Bienvenue, {first_name} ! Votre compte a été créé.")
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Erreur lors de l'inscription : {str(e)}")

    return render(request, 'accounts/register.html', {'is_auth_page': True})

@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect('profile_edit')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ProfileUpdateForm(instance=request.user)
        
    return render(request, 'accounts/profile_edit.html', {'form': form})


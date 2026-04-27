"""
Vues Gamification Complètes - Badges, Leaderboards, Stats Communautaires
Inspiré: Duolingo (badges), Discord (communities), Coursera (leaderboards)
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Avg, Count, Q, F
from django.utils import timezone
from datetime import timedelta, date
from django.core.paginator import Paginator

from .models import Badge, UserBadge, GlobalLeaderboard, XPAction, StreakRecord, Competition, CommunityContribution


# ===========================================================================
# DASHBOARD GAMIFICATION PRINCIPAL
# ===========================================================================

@login_required
def dashboard_gamification_view(request):
    """Dashboard principal gamification avec toutes les stats - Style Duolingo"""
    user = request.user
    
    # Récupérer streaks
    streak, created = StreakRecord.objects.get_or_create(user=user)
    
    # Stats immédiates
    xp_total = sum(action.points_gagnes for action in XPAction.objects.filter(user=user))
    
    # Badges récents non lus
    badges_recents = UserBadge.objects.filter(
        user=user,
        est_nouveau=True
    ).select_related('badge').order_by('-obtenu_at')[:5]
    
    # Total badges obtenus
    total_badges = UserBadge.objects.filter(user=user).count()
    
    # Dernières actions XP
    dernier_actions = XPAction.objects.filter(user=user).order_by('-created_at')[:10]
    
    # Classement utilisateur
    try:
        classement = GlobalLeaderboard.objects.filter(
            user=user,
            periode='all_time'
        ).first()
    except:
        classement = None
    
    # Top 10 leaderboard pour le dashboard
    classement_top_10 = GlobalLeaderboard.objects.filter(
        periode='all_time'
    ).order_by('-score_total')[:10]
    
    # Niveau XP
    niveau = calcule_niveau_xp(xp_total)
    
    # Calculer récompense quotidienne
    daily_reward_amount = 10 + (streak.streak_bonus_level * 5) if streak else 10
    
    context = {
        'streak': streak,
        'xp_total': xp_total,
        'niveau': niveau,
        'badges_recents': badges_recents,
        'total_badges': total_badges,
        'dernier_actions': dernier_actions,
        'classement': classement,
        'classement_top_10': classement_top_10,
        'has_daily_reward': streak.has_daily_reward(),
        'daily_reward_amount': daily_reward_amount,
    }
    
    return render(request, 'gamification/dashboard.html', context)


# ===========================================================================
# SYSTEME DE BADGES
# ===========================================================================

@login_required
def liste_badges_view(request):
    """Gallery complète des badges disponibles et obtenus"""
    categorie = request.GET.get('categorie', '')
    
    badges_queryset = Badge.objects.filter(est_actif=True)
    
    if categorie:
        badges_queryset = badges_queryset.filter(categorie=categorie)
    
    # Séparer badges obtenus vs non-obtenus
    badges_obtenus = UserBadge.objects.filter(user=request.user).values_list('badge_id', flat=True)
    
    paginator = Paginator(badges_queryset, 20)
    page = request.GET.get('page', 1)
    badges = paginator.get_page(page)
    
    context = {
        'badges': badges,
        'badges_obtenus': badges_obtenus,
        'categories': Badge.Categorie.choices,
        'selected_categorie': categorie,
    }
    
    return render(request, 'gamification/badges.html', context)


@login_required
def details_badge_view(request, badge_id):
    """Détails d'un badge spécifique + conditions d'obtention"""
    badge = get_object_or_404(Badge, id=badge_id)
    
    a_debloque = UserBadge.objects.filter(
        user=request.user,
        badge=badge
    ).exists()
    
    progression = 0
    if not a_debloque and badge.condition_obtention:
        progression = calcul_progression_badge(request.user, badge.condition_obtention)
    
    context = {
        'badge': badge,
        'a_debloque': a_debloque,
        'progression': progression,
    }
    
    return render(request, 'gamification/badge_detail.html', context)


@login_required
def attribuer_badge_manuellement(request, badge_id):
    """Attribution manuelle par admin/professeur"""
    if not hasattr(request.user, 'role') or request.user.role not in ['admin', 'professeur']:
        return HttpResponseForbidden("Accès refusé")
    
    target_user_id = request.POST.get('user_id')
    if not target_user_id:
        return redirect('gamification:liste_badges')
    
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target_user = User.objects.get(id=target_user_id)
        badge = Badge.objects.get(id=badge_id)
        
        badge.atribuer_a_utilisateur(target_user)
        
        from django.contrib import messages
        messages.success(request, f"Badge '{badge.nom}' attribué à {target_user.full_name}")
        
    except Exception as e:
        from django.contrib import messages
        messages.error(request, f"Erreur: {str(e)}")
    
    return redirect('gamification:liste_badges')


# ===========================================================================
# LEADERBOARDS
# ===========================================================================

@login_required
def leaderboard_mondial_view(request):
    """Leaderboard mondial inspiré de Coursera/Codeforces"""
    periode = request.GET.get('periode', 'all_time')
    filtre_pays = request.GET.get('pays', '')
    
    queryset = GlobalLeaderboard.objects.filter(periode=periode)
    
    if filtre_pays:
        queryset = queryset.filter(pays=filtre_pays)
    
    paginator = Paginator(queryset, 50)
    page = request.GET.get('page', 1)
    entries = paginator.get_page(page)
    
    try:
        user_entry = GlobalLeaderboard.objects.filter(
            user=request.user,
            periode=periode
        ).first()
        user_rang = user_entry.rang_mondial if user_entry else None
    except:
        user_rang = None
    
    context = {
        'entries': entries,
        'periode': periode,
        'user_rang': user_rang,
        'filtre_pays': filtre_pays,
    }
    
    return render(request, 'gamification/leaderboard.html', context)


@login_required
def leaderboard_classe_view(request):
    """Classement au sein de la classe de l'élève"""
    if not hasattr(request.user, 'role') or request.user.role != 'eleve':
        return redirect('gamification:leaderboard_mondial')
    
    classe = getattr(request.user, 'classe', None)
    if not classe:
        from django.contrib import messages
        messages.warning(request, "Votre classe n'est pas définie")
        return redirect('gamification:dashboard_gamification')
    
    entries = GlobalLeaderboard.objects.filter(
        user__composition_sessions__eleve=request.user,
        periode='all_time'
    ).distinct().order_by('-score_total')[:20]
    
    context = {
        'entries': entries,
        'classe': classe,
    }
    
    return render(request, 'gamification/leaderboard_classe.html', context)


# ===========================================================================
# SYSTEME XP
# ===========================================================================

@login_required
def historique_xp_view(request):
    """Historique complet gains XP"""
    actions = XPAction.objects.filter(user=request.user).order_by('-created_at')[:50]
    
    total_xp = sum(action.points_gagnes for action in actions)
    
    context = {
        'actions': actions,
        'total_xp': total_xp,
    }
    
    return render(request, 'gamification/historique_xp.html', context)


@login_required
def get_xp_stats_json(request):
    """API endpoints pour stats XP en temps réel (AJAX)"""
    user = request.user
    
    xp_total = sum(action.points_gagnes for action in XPAction.objects.filter(user=user))
    niveau = calcule_niveau_xp(xp_total)
    
    from_date = timezone.now() - timedelta(days=7)
    recent_actions = XPAction.objects.filter(
        user=user,
        created_at__gte=from_date
    )
    xp_7_jours = sum(action.points_gagnes for action in recent_actions)
    
    data = {
        'xp_total': xp_total,
        'niveau': niveau,
        'xp_derniere_semaine': xp_7_jours,
        'actions_derniere_semaine': recent_actions.count(),
    }
    
    return JsonResponse(data)


# ===========================================================================
# STREAKS & RECOMPENSES QUOTIDIENNES
# ===========================================================================

@login_required
def update_streak_view(request):
    """Mise à jour streak après connexion/activité"""
    streak, created = StreakRecord.objects.get_or_create(user=request.user)
    streak.update_streak()
    
    if streak.has_daily_reward():
        points = streak.claim_daily_reward()
        
        return JsonResponse({
            'success': True,
            'points_gagnes': points,
            'nouveau_streak': streak.current_streak,
            'multiplier': float(streak.streak_multiplier),
        })
    
    return JsonResponse({
        'success': True,
        'points_gagnes': 0,
        'streak': streak.current_streak,
    })


@login_required
def claim_daily_reward_view(request):
    """Réclamer récompense quotidienne manuellement"""
    streak, created = StreakRecord.objects.get_or_create(user=request.user)
    
    if not streak.has_daily_reward():
        return JsonResponse({
            'success': False,
            'error': 'Récompense déjà réclamée aujourd\'hui'
        }, status=400)
    
    points = streak.claim_daily_reward()
    
    return JsonResponse({
        'success': True,
        'points_gagnes': points,
        'nouveaux_stats': {
            'current_streak': streak.current_streak,
            'longest_streak': streak.longest_streak,
            'streak_bonus_level': streak.streak_bonus_level,
        }
    })


# ===========================================================================
# COMPETITIONS & EVENTS
# ===========================================================================

@login_required
def competitions_list_view(request):
    """Liste des compétitions actives et à venir"""
    competitions = Competition.objects.filter(
        status__in=['en_cours', 'preparation']
    ).order_by('-date_debut')
    
    context = {
        'competitions': competitions,
    }
    
    return render(request, 'gamification/competitions.html', context)


@login_required
def join_competition_view(request, competition_id):
    """Rejoindre une compétition"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    if competition.status != 'preparation':
        from django.http import Http404
        raise Http404("Compétition non joignable")
    
    competition.participants_count += 1
    competition.save(update_fields=['participants_count'])
    
    # Attribution XP immédiate (sans Celery)
    from django.contrib.auth.models import User as DjangoUser
    from .models import XPAction
    
    xp_action = XPAction.objects.create(
        user=request.user,
        action_type="participation_event",
        points_gagnes=10,
        description="Inscrit à la compétition",
        metadata={'competition_id': str(competition_id)}
    )
    
    return JsonResponse({'success': True, 'message': 'Inscrit avec succès!'})


# ===========================================================================
# COMMUNAUTE & CONTRIBUTIONS
# ===========================================================================

@login_required
def contributions_forum_view(request):
    """Forum communautaire type Discord/GitHub"""
    contributions = CommunityContribution.objects.all().select_related('contributor')[:50]
    
    if request.GET.get('sort') == 'recents':
        contributions = contributions.order_by('-created_at')
    else:
        contributions = contributions.order_by('-upvotes')
    
    context = {
        'contributions': contributions,
    }
    
    return render(request, 'gamification/forum.html', context)


@login_required
def create_contribution_view(request):
    """Créer une nouvelle contribution communautaire"""
    if request.method == 'POST':
        titre = request.POST.get('titre', '')
        contenu = request.POST.get('contenu', '')
        type_contrib = request.POST.get('type', 'reponse_aide')
        
        contribution = CommunityContribution.objects.create(
            contributor=request.user,
            type_contribution=type_contrib,
            titre=titre,
            contenu=contenu
        )
        
        # Attribution XP immédiate (sans Celery)
        from .models import XPAction
        
        xp_action = XPAction.objects.create(
            user=request.user,
            action_type="contribution_forum",
            points_gagnes=25,
            description="Publication dans le forum communautaire",
            metadata={'contribution_id': str(contribution.id)}
        )
        
        return JsonResponse({'success': True, 'message': 'Partagé avec succès!'})
    
    return render(request, 'gamification/create_contribution.html')


# ===========================================================================
# FONCTIONS UTILITAIRES
# ===========================================================================

def calcule_niveau_xp(xp_total: int) -> int:
    """Calcule le niveau basé sur l'XP total (courbe exponentielle)"""
    if xp_total < 100:
        return 1
    elif xp_total < 300:
        return 2
    elif xp_total < 600:
        return 3
    elif xp_total < 1000:
        return 4
    elif xp_total < 1500:
        return 5
    elif xp_total < 2200:
        return 6
    elif xp_total < 3000:
        return 7
    elif xp_total < 4000:
        return 8
    elif xp_total < 5200:
        return 9
    elif xp_total < 6600:
        return 10
    elif xp_total < 8200:
        return 11
    elif xp_total < 10000:
        return 12
    else:
        return max(20, xp_total // 1000)


def calcul_progression_badge(user, conditions: dict) -> int:
    """Calcule la progression (%) vers un badge donné"""
    if 'compositions' in conditions:
        nb_requis = conditions['compositions']
        nb_realises = user.composition_sessions.count()
        if nb_realises >= nb_requis:
            return 100
        return int((nb_realises / nb_requis) * 100)
    
    return 0

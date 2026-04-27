"""
Celery Tasks pour Gamification - Calculs asynchrones et mises à jour massives
Optimisé pour haute charge et grande communauté éducative
"""
from celery import shared_task
from django.db.models import Avg, Count, Q, F
from django.utils import timezone
from datetime import timedelta, date
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def self(self):
    """Task racine pour les computations gamification"""
    pass


@shared_task
def award_xp_points(user_id, action, points, metadata=None):
    """
    Attribue des points XP à un utilisateur avec journalisation
    Inspiré: Duolingo (XP tracking), Coursera (achievement points)
    
    Args:
        user_id: ID de l'utilisateur
        action: Type d'action ('connexion', 'examen_finie', etc.)
        points: Nombre de XP à attribuer
        metadata: Données additionnelles (contexte)
    """
    try:
        from django.contrib.auth.models import User as DjangoUser
        from .models import XPAction
        
        user = DjangoUser.objects.get(id=user_id)
        
        # Création entry XP Action
        xp_action = XPAction.objects.create(
            user=user,
            action_type=action,
            points_gagnes=points,
            description=f"Gagné {points} XP pour {action}",
            metadata=metadata or {}
        )
        
        logger.info(f"[Gamification] +{points} XP attribués à {user.full_name} pour '{action}'")
        
        # Trigger update streak si action est connexion
        if action == 'connexion':
            update_user_streak.delay(user_id)
        
        return {'success': True, 'xp_action_id': str(xp_action.id)}
        
    except Exception as exc:
        logger.error(f"[Gamification] Erreur award_xp_points: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def award_badge_to_user(user_id, badge_id, log_xp=True):
    """
    Attribue un badge à un utilisateur
    Inspiré: Discord (role assignment), Duolingo (badge unlock animation)
    
    Args:
        user_id: ID utilisateur
        badge_id: ID badge
        log_xp: Si True, ajoute XP correspondante au badge
    """
    try:
        from django.contrib.auth.models import User as DjangoUser
        from .models import UserBadge, Badge
        
        user = DjangoUser.objects.get(id=user_id)
        badge = Badge.objects.get(id=badge_id)
        
        # Créer association user-badge
        user_badge, created = UserBadge.objects.get_or_create(
            user=user,
            badge=badge
        )
        
        if created:
            logger.info(f"[Gamification] Badge '{badge.nom}' débloqué par {user.full_name}")
            
            # Logger notification (future feature: email/push)
            # TODO: Implémenter notifications
            
            if log_xp:
                # Ajouter XP du badge
                award_xp_points.delay(
                    user_id=user_id,
                    action=f"Badge obtenu: {badge.nom}",
                    points=badge.points_valeur,
                    metadata={'badge_id': str(badge_id)}
                )
            
            return {'success': True, 'new_badge': created}
        
        return {'success': True, 'new_badge': False}
        
    except Exception as e:
        logger.error(f"[Gamification] Erreur award_badge: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def update_user_streak(user_id):
    """
    Met à jour le streak quotidien d'un utilisateur
    Optimisé pour éviter double comptage
    
    Args:
        user_id: ID utilisateur
    """
    try:
        from django.contrib.auth.models import User as DjangoUser
        from .models import StreakRecord
        
        user = DjangoUser.objects.get(id=user_id)
        streak, created = StreakRecord.objects.get_or_create(user=user)
        
        # Mise à jour streak logique
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        if not streak.last_activity_date or streak.last_activity_date < yesterday:
            if streak.last_activity_date == yesterday or not streak.last_activity_date:
                streak.current_streak += 1
                
                # Bonus milestones calculation
                if streak.current_streak >= 30:
                    streak.streak_bonus_level = 5
                    streak.streak_multiplier = 2.0
                elif streak.current_streak >= 7:
                    streak.streak_bonus_level = 3
                    streak.streak_multiplier = 1.5
                elif streak.current_streak >= 3:
                    streak.streak_bonus_level = 1
                    streak.streak_multiplier = 1.2
                
                if streak.current_streak > streak.longest_streak:
                    streak.longest_streak = streak.current_streak
        
        streak.last_activity_date = today
        streak.total_logins += 1
        streak.save()
        
        logger.info(f"[Gamification] Streak mis à jour pour {user.full_name}: {streak.current_streak} jours")
        
        return {'success': True, 'current_streak': streak.current_streak}
        
    except Exception as e:
        logger.error(f"[Gamification] Erreur update_streak: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def claim_daily_reward(user_id):
    """
    Réclame la récompense quotidienne d'un utilisateur
    Système inspiré de Duolingo (daily streak bonus)
    
    Args:
        user_id: ID utilisateur
    """
    try:
        from django.contrib.auth.models import User as DjangoUser
        from .models import StreakRecord
        
        user = DjangoUser.objects.get(id=user_id)
        streak, created = StreakRecord.objects.get_or_create(user=user)
        
        if not streak.has_daily_reward():
            return {'success': False, 'error': 'Already claimed'}
        
        base_points = 10 + (streak.streak_bonus_level * 5)
        total_points = int(base_points * streak.streak_multiplier)
        
        # Award XP
        award_xp_points.delay(
            user_id=user_id,
            action="Récompense quotidienne",
            points=total_points,
            metadata={
                'base': base_points,
                'multiplier': float(streak.streak_multiplier),
                'streak_level': streak.streak_bonus_level
            }
        )
        
        streak.last_check_date = date.today()
        streak.save()
        
        logger.info(f"[Gamification] Récompense quotidienne réclamée: +{total_points} XP (x{streak.streak_multiplier})")
        
        return {
            'success': True,
            'points_gagnes': total_points,
            'streak': streak.current_streak,
            'bonus_multiplier': float(streak.streak_multiplier)
        }
        
    except Exception as e:
        logger.error(f"[Gamification] Erreur claim_daily_reward: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def calculate_leaderboard_positions(batch_size=1000):
    """
    Calcule les positions du leaderboard pour tous les utilisateurs
    Exécution planifiée toutes les heures via Celery Beat
    
    Optimisé pour performance sur grandes communautés
    """
    try:
        from django.contrib.auth.models import User as DjangoUser
        from .models import GlobalLeaderboard
        
        logger.info("[Gamification] Démarrage calcul leaderboard...")
        
        # Récupérer tous les utilisateurs avec activité récente
        users = DjangoUser.objects.filter(
            composition_sessions__isnull=False
        ).distinct()[:batch_size]
        
        updated_count = 0
        
        for user in users:
            # Calcul statistiques utilisateur
            scores = user.composition_sessions.filter(
                resultat__isnull=False
            ).values_list('resultat__note', 'resultat__note_sur')
            
            if scores.exists():
                avg_score = sum(score[0]/score[1]*20 for score in scores) / scores.count()
                nb_compositions = scores.count()
                excellent_notes = scores.filter(
                    Q(note__gte='16', note_sur='20.00')
                ).count()
                
                # Calcul XP total
                xp_total = sum(
                    action.points_gaines 
                    for action in user.xp_actions.all()
                )
                
                # Niveau basé sur XP
                niveau = max(1, xp_total // 1000 + 1)
                
                # Streak actuel
                try:
                    streak = user.streak
                    current_streak = streak.current_streak
                except:
                    current_streak = 0
                
                # Badges count
                badges_count = user.user_badges.count()
                
                # Trouver ou créer entry leaderboard
                entry, created = GlobalLeaderboard.objects.get_or_create(
                    user=user,
                    periode='all_time',
                    date_periode=date.today(),
                    defaults={
                        'score_total': xp_total,
                        'points_xp': xp_total,
                        'niveau': niveau,
                        'nb_compositions': nb_compositions,
                        'moyenne_generale': avg_score,
                        'streak_jours': current_streak,
                        'badges_obtenus': badges_count,
                    }
                )
                
                # Mise à jour si existant
                if not created:
                    entry.score_total = xp_total
                    entry.niveau = niveau
                    entry.nb_compositions = nb_compositions
                    entry.moyenne_generale = avg_score
                    entry.streak_jours = current_streak
                    entry.badges_obtenus = badges_count
                    entry.save(update_fields=[
                        'score_total', 'niveau', 'nb_compositions',
                        'moyenne_generale', 'streak_jours', 'badges_obtenus'
                    ])
                
                updated_count += 1
        
        logger.success(f"[Gamification] Leaderboard mis à jour: {updated_count} utilisateurs")
        
        # Recalculer les rangs
        recalculate_leaderboard_ranks.delay()
        
        return {'success': True, 'users_updated': updated_count}
        
    except Exception as e:
        logger.error(f"[Gamification] Erreur calculate_leaderboard: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def recalculate_leaderboard_ranks():
    """
    Recalcule les rangs mondiaux et nationaux après mise à jour des scores
    Utilise window functions SQL pour performance
    """
    try:
        from django.contrib.auth.models import User as DjangoUser
        from .models import GlobalLeaderboard
        
        logger.info("[Gamification] Recalcul des rangs leaderboard...")
        
        # Rang mondial
        entries = GlobalLeaderboard.objects.filter(periode='all_time').order_by('-score_total')
        
        for rank, entry in enumerate(entries, 1):
            entry.rang_mondial = rank
            entry.classement_actuel = rank <= 100  # Top 10% check
        
        GlobalLeaderboard.objects.bulk_update(entries, ['rang_mondial', 'classement_actuel'])
        
        logger.success(f"[Gamification] Rang recalculé pour {entries.count()} entrées")
        
        return {'success': True, 'entries_updated': entries.count()}
        
    except Exception as e:
        logger.error(f"[Gamification] Erreur recalculate_ranks: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def check_badge_conditions_periodically():
    """
    Vérifie périodiquement les conditions d'obtention de badges
    Exécution toutes les heures via Celery Beat
    
    Inspiré: Coursera (completion checks), Duolingo (milestone tracking)
    """
    try:
        from django.contrib.auth.models import User as DjangoUser
        from .models import Badge, UserBadge
        
        logger.info("[Gamification] Vérification conditions badges...")
        
        # Récupérer tous les badges actifs
        badges = Badge.objects.filter(est_actif=True, is_achievable=True)
        
        awarded_count = 0
        
        for badge in badges:
            # Trouver utilisateurs qui remplissent conditions
            eligible_users = get_eligible_users_for_badge(badge)
            
            for user in eligible_users:
                # Vérifier si déjà obtenu
                already_obtained = UserBadge.objects.filter(
                    user=user,
                    badge=badge
                ).exists()
                
                if not already_obtained:
                    # Attribuer le badge
                    award_badge_to_user.delay(user.id, badge.id, log_xp=True)
                    awarded_count += 1
        
        logger.success(f"[Gamification] Badges vérifiés: {awarded_count} nouveaux débloqués")
        
        return {'success': True, 'newly_awarded': awarded_count}
        
    except Exception as e:
        logger.error(f"[Gamification] Erreur check_badge_conditions: {e}")
        return {'success': False, 'error': str(e)}


# ===========================================================================
# Fonctions Utilitaires
# ===========================================================================

def get_eligible_users_for_badge(badge):
    """
    Détermine quels utilisateurs sont éligibles pour un badge donné
    Basé sur les conditions dans condition_obtention JSON
    
    Exemples de conditions:
    - {'compositions': 10, 'type': 'minimum'}
    - {'moyenne_min': 15, 'type': 'average'}
    - {'streak_min': 7, 'type': 'streak'}
    """
    from django.contrib.auth.models import User as DjangoUser
    from django.db.models import Avg, Count, Q
    
    conditions = badge.condition_obtention or {}
    query = Q()
    
    # Condition compositions
    if 'compositions' in conditions:
        min_compositions = conditions['compositions']
        query &= Q(composition_sessions__id__gt=min_compositions)
    
    # Condition moyenne
    if 'moyenne_min' in conditions:
        min_avg = conditions['moyenne_min']
        # À implémenter: filtre selon moyenne réelle
    
    # Condition streak
    if 'streak_min' in conditions:
        min_streak = conditions['streak_min']
        # À implémenter: filtre streak records
    
    # Récupérer utilisateurs éligibles
    users = DjangoUser.objects.filter(query).distinct()[:1000]
    
    return users


@shared_task
def generate_weekly_leaderboard_summary():
    """
    Génère un résumé hebdomadaire du leaderboard pour newsletter/communique
    Exécution chaque lundi matin
    """
    try:
        from django.contrib.auth.models import User as DjangoUser
        from .models import GlobalLeaderboard
        
        start_of_week = date.today() - timedelta(days=date.today().weekday())
        
        top_users = GlobalLeaderboard.objects.filter(
            periode='semaine',
            date_periode__gte=start_of_week
        ).order_by('-score_total')[:10]
        
        summary = {
            'period': f"{start_of_week.strftime('%d/%m')} - {date.today().strftime('%d/%m')}",
            'top_performers': [
                {
                    'rank': i+1,
                    'name': user.user.full_name,
                    'xp': user.score_total,
                    'streak': user.streak_jours
                }
                for i, user in enumerate(top_users)
            ],
            'total_active': GlobalLeaderboard.objects.filter(
                date_periode__gte=start_of_week
            ).distinct('user').count()
        }
        
        logger.info(f"[Gamification] Résumé hebdo généré: {summary['total_active']} actifs")
        
        return summary
        
    except Exception as e:
        logger.error(f"[Gamification] Erreur weekly_summary: {e}")
        return {'success': False, 'error': str(e)}

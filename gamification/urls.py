from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    path('dashboard/', views.dashboard_gamification_view, name='dashboard_gamification'),
    path('badges/', views.liste_badges_view, name='liste_badges'),
    path('badges/<uuid:badge_id>/', views.details_badge_view, name='details_badge'),
    path('badges/<uuid:badge_id>/attribuer/', views.attribuer_badge_manuellement, name='attribuer_badge'),
    path('leaderboard/mondial/', views.leaderboard_mondial_view, name='leaderboard_mondial'),
    path('leaderboard/classe/', views.leaderboard_classe_view, name='leaderboard_classe'),
    path('xp/historique/', views.historique_xp_view, name='historique_xp'),
    path('xp/stats/', views.get_xp_stats_json, name='xp_stats_json'),
    path('streak/update/', views.update_streak_view, name='update_streak'),
    path('streak/claim-reward/', views.claim_daily_reward_view, name='claim_daily_reward'),
    path('competitions/', views.competitions_list_view, name='competitions_list'),
    path('competitions/<uuid:competition_id>/join/', views.join_competition_view, name='join_competition'),
    path('contributions/', views.contributions_forum_view, name='contributions_forum'),
    path('contributions/create/', views.create_contribution_view, name='create_contribution'),
]

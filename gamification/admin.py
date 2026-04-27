from django.contrib import admin
from .models import Badge, UserBadge, GlobalLeaderboard, XPAction, StreakRecord


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['nom', 'icone', 'categorie', 'points', 'rarete', 'est_actif']
    list_filter = ['categorie', 'rarete', 'est_actif']
    search_fields = ['nom']


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge', 'obtenu_at', 'est_nouveau']
    list_filter = ['est_nouveau']


@admin.register(GlobalLeaderboard)
class GlobalLeaderboardAdmin(admin.ModelAdmin):
    list_display = ['user', 'periode', 'rang_mondial', 'score_total', 'niveau', 'pays']
    list_filter = ['periode', 'pays']
    search_fields = ['user__email']


@admin.register(XPAction)
class XPActionAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'points_gagnes', 'created_at']


@admin.register(StreakRecord)
class StreakRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_streak', 'longest_streak', 'last_activity_date']

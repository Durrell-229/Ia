from django.contrib import admin
from .models import Notification, EmailQueue, GlobalAnnouncement


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'type', 'title', 'is_read', 'created_at']
    list_filter = ['type', 'is_read']
    search_fields = ['recipient__email', 'title']


@admin.register(EmailQueue)
class EmailQueueAdmin(admin.ModelAdmin):
    list_display = ['destinataire', 'sujet', 'statut', 'tentatives', 'created_at']
    list_filter = ['statut']
    search_fields = ['destinataire', 'sujet']

@admin.register(GlobalAnnouncement)
class GlobalAnnouncementAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_alerte', 'est_actif', 'date_expiration', 'created_at']
    list_filter = ['type_alerte', 'est_actif']
    search_fields = ['titre', 'message']

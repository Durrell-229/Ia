from django.contrib import admin
from .models import VideoAnnouncement


@admin.register(VideoAnnouncement)
class VideoAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'order', 'is_active', 'auto_play', 'created_at')
    list_filter = ('category', 'is_active', 'auto_play')
    search_fields = ('title', 'description')
    list_editable = ('order', 'is_active')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Informations', {
            'fields': ('title', 'description', 'category', 'order')
        }),
        ('Médias', {
            'fields': ('video_file', 'thumbnail'),
            'description': 'Placez vos vidéos dans: media/showcase_videos/'
        }),
        ('Options', {
            'fields': ('is_active', 'auto_play')
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_alerte', 'recipient', 'is_read', 'created_at')
    list_filter = ('type_alerte', 'is_read', 'created_at')
    search_fields = ('titre', 'message')
    list_editable = ('is_read',)
    
    def save_model(self, request, obj, form, change):
        # Logique optionnelle ici pour déclencher des emails ou des pushs
        super().save_model(request, obj, form, change)

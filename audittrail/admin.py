from django.contrib import admin
from .models import AuditLog, DataExport


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'resource_type', 'severity', 'timestamp']
    list_filter = ['action', 'severity', 'timestamp']
    search_fields = ['description', 'user__email']
    readonly_fields = [f.name for f in AuditLog._meta.get_fields()]


@admin.register(DataExport)
class DataExportAdmin(admin.ModelAdmin):
    list_display = ['demandeur', 'type_export', 'format_export', 'nb_lignes', 'created_at']
    list_filter = ['format_export', 'type_export']

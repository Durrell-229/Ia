from django.contrib import admin
from .models import AICorrection, CorrectionDetail


class CorrectionDetailInline(admin.TabularInline):
    model = CorrectionDetail
    extra = 0


@admin.register(AICorrection)
class AICorrectionAdmin(admin.ModelAdmin):
    list_display = ['resultat', 'note_proposee', 'model_utilise', 'statut', 'created_at']
    list_filter = ['statut', 'model_utilise']
    search_fields = ['resultat__session__eleve__email']
    inlines = [CorrectionDetailInline]

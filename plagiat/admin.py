from django.contrib import admin
from .models import PlagiarismCheck, PlagiarismPair, PlagiarismReport


@admin.register(PlagiarismCheck)
class PlagiarismCheckAdmin(admin.ModelAdmin):
    list_display = ['exam', 'statut', 'nb_paires_analysees', 'nb_paires_suspectes', 'created_at']
    list_filter = ['statut']


@admin.register(PlagiarismPair)
class PlagiarismPairAdmin(admin.ModelAdmin):
    list_display = ['session_1', 'session_2', 'similarite_globale', 'niveau_suspection']
    list_filter = ['niveau_suspection']


@admin.register(PlagiarismReport)
class PlagiarismReportAdmin(admin.ModelAdmin):
    list_display = ['check', 'resume', 'created_at']

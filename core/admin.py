from django.contrib import admin
from .models import Matiere, Classe, Parametre


@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'couleur', 'is_active']
    search_fields = ['nom', 'code']
    list_filter = ['is_active']


@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ['nom', 'niveau', 'section', 'annee_academique', 'is_active']
    search_fields = ['nom', 'section']
    list_filter = ['niveau', 'annee_academique']


@admin.register(Parametre)
class ParametreAdmin(admin.ModelAdmin):
    list_display = ['cle', 'description']
    search_fields = ['cle', 'description']

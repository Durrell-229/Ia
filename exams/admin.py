from django.contrib import admin
from .models import Exam, ExamFile, ExamAssignment


class ExamFileInline(admin.TabularInline):
    model = ExamFile
    extra = 1


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_exam', 'matiere', 'classe', 'createur', 'statut', 'date_debut', 'date_fin']
    list_filter = ['type_exam', 'statut', 'matiere', 'classe']
    search_fields = ['titre', 'description']
    inlines = [ExamFileInline]
    date_hierarchy = 'date_debut'


@admin.register(ExamAssignment)
class ExamAssignmentAdmin(admin.ModelAdmin):
    list_display = ['exam', 'eleve', 'classe', 'assigned_by', 'assigned_at']
    list_filter = ['assigned_at']
    search_fields = ['exam__titre', 'eleve__email']

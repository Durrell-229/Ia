from django.contrib import admin
from .models import CompositionSession, StudentAnswer, StudentSubmissionFile, Resultat, AntiCheatLog


class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 0


class StudentSubmissionFileInline(admin.TabularInline):
    model = StudentSubmissionFile
    extra = 0


class AntiCheatLogInline(admin.TabularInline):
    model = AntiCheatLog
    extra = 0
    readonly_fields = ['type_event', 'description', 'timestamp']


@admin.register(CompositionSession)
class CompositionSessionAdmin(admin.ModelAdmin):
    list_display = ['exam', 'eleve', 'mode', 'statut', 'started_at', 'submitted_at', 'cheat_count']
    list_filter = ['mode', 'statut', 'exam']
    search_fields = ['exam__titre', 'eleve__email', 'eleve__first_name']
    inlines = [StudentAnswerInline, StudentSubmissionFileInline, AntiCheatLogInline]


@admin.register(Resultat)
class ResultatAdmin(admin.ModelAdmin):
    list_display = ['session', 'note', 'note_sur', 'mention', 'classement', 'corrige_par_ia', 'corrige_at']
    list_filter = ['mention', 'corrige_par_ia', 'corrige_par_humain']
    search_fields = ['session__eleve__email', 'session__exam__titre']


@admin.register(AntiCheatLog)
class AntiCheatLogAdmin(admin.ModelAdmin):
    list_display = ['session', 'type_event', 'timestamp']
    list_filter = ['type_event', 'timestamp']

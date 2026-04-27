from django.contrib import admin
from .models import QuestionBank, Choice, QCMExam, QCMExamQuestion, QCMAnswer


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ['texte_trunc', 'matiere', 'difficulte', 'createur', 'est_publique', 'generee_par_ia']
    list_filter = ['difficulte', 'est_publique', 'generee_par_ia', 'matiere']
    search_fields = ['texte']
    inlines = [ChoiceInline]

    def texte_trunc(self, obj):
        return obj.texte[:60] + '...' if len(obj.texte) > 60 else obj.texte
    texte_trunc.short_description = 'Texte'


@admin.register(QCMExam)
class QCMExamAdmin(admin.ModelAdmin):
    list_display = ['exam', 'mode_notation', 'melanger_questions', 'afficher_resultat_immediat']


@admin.register(QCMAnswer)
class QCMAnswerAdmin(admin.ModelAdmin):
    list_display = ['session', 'question', 'est_correct', 'points_obtenus', 'answered_at']
    list_filter = ['est_correct']

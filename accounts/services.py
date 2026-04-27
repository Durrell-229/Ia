from django.db.models import Avg, Count
from exams.models import Exam
from django.contrib.auth import get_user_model

User = get_user_model()

class DashboardService:
    @staticmethod
    def get_prof_stats(user):
        from correction.models import CorrectionCopie
        return {
            'pending_corrections': CorrectionCopie.objects.filter(exam__createur=user, status='pending').count(),
            'avg_class_success': CorrectionCopie.objects.filter(exam__createur=user).aggregate(Avg('grade'))['grade__avg'] or 0,
        }

    @staticmethod
    def get_student_stats(user):
        from correction.models import CorrectionCopie
        from gamification.models import UserBadge
        return {
            'completed_exams': CorrectionCopie.objects.filter(student=user, status='approved').count(),
            'total_badges': UserBadge.objects.filter(user=user).count(),
            'next_exams': Exam.objects.filter(
                assignments__eleve=user,
                statut='publie'
            ).count() if user else 0
        }

    @staticmethod
    def get_cp_stats():
        return {
            'total_profs': User.objects.filter(role='professeur').count(),
            'total_eleves': User.objects.filter(role='eleve').count(),
            'pending_approvals': Exam.objects.filter(approval_status='pending').count(),
        }

    @staticmethod
    def get_admin_stats():
        return {
            'total_users': User.objects.count(),
            'api_status': "Opérationnel",
            'recent_logs': 5 # Dummy count
        }

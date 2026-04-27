from django.core.mail import send_mail
from django.conf import settings
from .models import Notification

class NotificationService:
    @staticmethod
    def notify(user, title, message, type='APPROBATION'):
        # 1. Enregistrer en base
        Notification.objects.create(
            recipient=user,
            title=title,
            message=message,
            type=type
        )
        
        # 2. Envoyer par email
        try:
            send_mail(
                subject=title,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Erreur envoi email: {e}")

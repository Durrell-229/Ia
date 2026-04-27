import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import EmailQueue, Notification

logger = logging.getLogger(__name__)


@shared_task
def send_notification_email(notification_id: str):
    try:
        notif = Notification.objects.get(id=notification_id)

        send_mail(
            subject=notif.title,
            message=notif.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notif.recipient.email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Erreur envoi email notification {notification_id}: {e}")


@shared_task
def process_email_queue():
    pending = EmailQueue.objects.filter(statut=EmailQueue.Statut.EN_ATTENTE, tentatives__lt=3)[:50]
    for email in pending:
        try:
            kwargs = {
                'subject': email.sujet,
                'message': email.corps_texte or '',
                'from_email': settings.DEFAULT_FROM_EMAIL,
                'recipient_list': [email.destinataire],
                'html_message': email.corps_html,
                'fail_silently': False,
            }
            if email.piece_jointe:
                from django.core.mail import EmailMessage
                msg = EmailMessage(
                    subject=email.sujet,
                    body=email.corps_html,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email.destinataire],
                )
                msg.content_subtype = 'html'
                msg.attach_file(email.piece_jointe.path)
                msg.send()
            else:
                send_mail(**kwargs)

            email.statut = EmailQueue.Statut.ENVOYE
            email.sent_at = timezone.now()
            email.save()
        except Exception as e:
            email.tentatives += 1
            email.erreur = str(e)
            if email.tentatives >= 3:
                email.statut = EmailQueue.Statut.ERREUR
            email.save()


@shared_task
def create_and_send_notification(user_id: str, type_notif: str, titre: str, message: str, lien: str = ''):
    from accounts.models import User
    user = User.objects.get(id=user_id)
    notif = Notification.objects.create(
        recipient=user,
        type=type_notif,
        title=titre,
        message=message,
    )
    send_notification_email.delay(str(notif.id))

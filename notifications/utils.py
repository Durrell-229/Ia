from .models import Notification

def send_notification(user, title, message, link=None, type='INSCRIPTION'):
    """Crée une notification en base de données pour un utilisateur."""
    return Notification.objects.create(
        recipient=user,
        title=title,
        message=message,
        type=type
    )

"""
Custom template tags pour notifications
"""
from django import template

register = template.Library()


@register.filter
def dict_get(dictionary, key):
    """Récupérer une valeur d'un dictionnaire par clé (comme get en Python)"""
    if dictionary is None:
        return False
    return dictionary.get(key, False)


@register.filter
def replace(value, args):
    """Remplacer des caractères dans une chaîne"""
    if not value:
        return ''
    old, new = args.split(':')
    return value.replace(old, new)


@register.simple_tag
def notification_count(user):
    """Compter les notifications non-lues pour un utilisateur"""
    from .models import Notification
    
    if user.is_authenticated:
        count = Notification.objects.filter(
            destinateur=user,
            is_read=False,
            is_deleted_for_user=False
        ).count()
        return count
    return 0


@register.simple_tag(takes_context=True)
def current_url(context):
    """Retourner l'URL actuelle de la page"""
    return context['request'].get_full_path()

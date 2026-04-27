from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class CoursConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cours'
    verbose_name = _('Gestion des Cours')

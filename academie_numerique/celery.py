import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academie_numerique.settings')

app = Celery('academie_numerique')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

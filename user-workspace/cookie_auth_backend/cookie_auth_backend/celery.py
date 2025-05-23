import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cookie_auth_backend.settings')

app = Celery('cookie_auth_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "projet.settings")

app = Celery("projet")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

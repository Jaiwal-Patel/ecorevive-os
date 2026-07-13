import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecorevive.settings")

app = Celery("ecorevive")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

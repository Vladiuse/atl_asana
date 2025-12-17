import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "atl_asana.settings")

app = Celery("atl_asana")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

from .celery_signals import notify_in_telegram  # noqa: E402, F401

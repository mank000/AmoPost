# project_name/celery.py
import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("amopost")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "fetch-notifications-every-5-min": {
        "task": "farpost.tasks.fetch_notifications",
        "schedule": crontab(minute="*/1"),
    },
}
app.conf.timezone = "Europe/Amsterdam"

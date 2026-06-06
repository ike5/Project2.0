"""
Celery application.

Reads its config from Django settings (the `CELERY_*` keys) and autodiscovers
`tasks.py` in every installed app. Imported by config/__init__.py so `shared_task`
works everywhere.
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("slack")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")

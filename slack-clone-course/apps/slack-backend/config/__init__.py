# Ensure the Celery app is imported when Django starts so shared_task works.
# (The celery module is added in Module 07; the import is guarded until then.)
try:
    from .celery import app as celery_app  # noqa: F401

    __all__ = ("celery_app",)
except ImportError:  # Celery not configured yet (pre-Module 07)
    pass

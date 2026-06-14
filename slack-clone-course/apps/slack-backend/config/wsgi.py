"""WSGI entrypoint (sync HTTP only). Used by gunicorn if you don't need WebSockets.
In production we serve via ASGI (config/asgi.py) so Channels works — see Module 12."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()

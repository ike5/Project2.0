from django.apps import AppConfig


class WebhooksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "webhooks"

    def ready(self):
        # Connect the post_save signal that fires outgoing webhooks.
        from . import signals  # noqa: F401

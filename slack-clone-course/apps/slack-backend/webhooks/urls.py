"""Webhook routes (mounted under /api/webhooks/)."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import IncomingWebhookView, IncomingWebhookViewSet, OutgoingWebhookViewSet

router = DefaultRouter()
router.register("incoming", IncomingWebhookViewSet, basename="incoming-webhook")
router.register("outgoing", OutgoingWebhookViewSet, basename="outgoing-webhook")

urlpatterns = [
    # Public endpoint external tools POST to (token is the credential).
    path("in/<str:token>/", IncomingWebhookView.as_view(), name="incoming-webhook"),
    *router.urls,
]

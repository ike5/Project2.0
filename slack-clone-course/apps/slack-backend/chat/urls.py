"""Chat API routes (mounted under /api/)."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .uploads import AttachmentViewSet, presign_upload, search
from .views import ChannelViewSet, MessageViewSet

router = DefaultRouter()
router.register("channels", ChannelViewSet, basename="channel")
router.register("messages", MessageViewSet, basename="message")
router.register("attachments", AttachmentViewSet, basename="attachment")  # Module 11

urlpatterns = [
    path("uploads/presign/", presign_upload, name="presign-upload"),  # Module 11
    path("search/", search, name="search"),                           # Module 11
    *router.urls,
]

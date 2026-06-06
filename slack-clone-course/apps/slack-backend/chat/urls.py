"""Chat API routes (mounted under /api/)."""
from rest_framework.routers import DefaultRouter

from .views import ChannelViewSet, MessageViewSet

router = DefaultRouter()
router.register("channels", ChannelViewSet, basename="channel")
router.register("messages", MessageViewSet, basename="message")

urlpatterns = router.urls

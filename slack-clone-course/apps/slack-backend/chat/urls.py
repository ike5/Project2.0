"""Chat API routes. Channels/messages viewsets are registered in Module 04."""
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
# Module 04 registers:
# router.register("channels", ChannelViewSet)
# router.register("messages", MessageViewSet)

urlpatterns = router.urls

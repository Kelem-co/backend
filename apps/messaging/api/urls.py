from messaging.api.views import ThreadViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("chat-threads", ThreadViewSet, basename="chat-thread")

urlpatterns = router.urls

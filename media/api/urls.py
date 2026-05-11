from django.urls import include
from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import MediaUploadViewSet

router = SimpleRouter(trailing_slash=False)
router.register(r"media", MediaUploadViewSet, basename="media")

app_name = "media"

urlpatterns = [
    path("", include(router.urls)),
]

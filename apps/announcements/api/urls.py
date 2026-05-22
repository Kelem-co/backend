from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AnnouncementViewSet

app_name = "announcements"

router = DefaultRouter()
router.register(r"announcements", AnnouncementViewSet, basename="announcement")

urlpatterns = [
    path("", include(router.urls)),
]

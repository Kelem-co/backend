from django.conf import settings
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from accounts.api.views import UserViewSet
from organizations.api.views import OrganizationViewSet
from schools.api.views import BranchAdminViewSet, BranchViewSet, SchoolViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("users", UserViewSet)
router.register("organizations", OrganizationViewSet)
router.register("schools", SchoolViewSet)
router.register("branches", BranchViewSet)
router.register("branch-admins", BranchAdminViewSet)


app_name = "api"
urlpatterns = router.urls

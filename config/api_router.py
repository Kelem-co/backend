from accounts.api.views import UserViewSet
from academics.api.views import (
    AcademicYearViewSet,
    GradeViewSet,
    SectionViewSet,
    SubjectViewSet,
)
from branches.api.views import BranchAdminViewSet, BranchViewSet
from django.conf import settings
from organizations.api.views import OrganizationViewSet
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter
from schools.api.views import SchoolViewSet
from students.api.views import StudentViewSet, ParentStudentLinkViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()


router.register("users", UserViewSet)
router.register("organizations", OrganizationViewSet)
router.register("schools", SchoolViewSet)
router.register("branches", BranchViewSet)
router.register("branch-admins", BranchAdminViewSet)
router.register("academic-years", AcademicYearViewSet)
router.register("grades", GradeViewSet)
router.register("sections", SectionViewSet)
router.register("subjects", SubjectViewSet)
router.register("students", StudentViewSet)
router.register("parent-links", ParentStudentLinkViewSet)



app_name = "api"
urlpatterns = router.urls

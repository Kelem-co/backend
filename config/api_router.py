from academics.api.views import AcademicYearViewSet
from academics.api.views import GradeSubjectViewSet
from academics.api.views import GradeViewSet
from academics.api.views import SectionViewSet
from academics.api.views import SubjectViewSet
from accounts.api.views import UserViewSet
from analytics.api.views import InterventionLogViewSet
from announcements.api.views import AnnouncementViewSet
from assessments.api.views import AssessmentResultViewSet
from assessments.api.views import AssessmentViewSet
from attendance.api.views import AttendanceReasonViewSet
from attendance.api.views import AttendanceSummaryViewSet
from attendance.api.views import AttendanceViewSet
from branches.api.views import BranchAdminCompleteInvitationView
from branches.api.views import BranchAdminInviteView
from branches.api.views import BranchAdminViewSet
from branches.api.views import BranchViewSet
from django.conf import settings
from django.urls import include
from django.urls import path
from organizations.api.views import OrganizationViewSet
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter
from schools.api.views import SchoolViewSet
from students.api.views import ParentStudentLinkViewSet
from students.api.views import ParentViewSet
from students.api.views import StudentViewSet
from teachers.api.views import HomeroomAssignmentViewSet
from teachers.api.views import TeacherQualificationViewSet
from teachers.api.views import TeacherSubjectAssignmentViewSet
from teachers.api.views import TeacherViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()


router.register("users", UserViewSet)
router.register("organizations", OrganizationViewSet)
router.register("schools", SchoolViewSet)
router.register("branches", BranchViewSet)
router.register("branch-admins", BranchAdminViewSet)
router.register("academic-years", AcademicYearViewSet)
router.register("grades", GradeViewSet)
router.register("grade-subjects", GradeSubjectViewSet, basename="grade-subject")
router.register("sections", SectionViewSet)
router.register("subjects", SubjectViewSet)
router.register("students", StudentViewSet, basename="student")
router.register("parents", ParentViewSet, basename="parent")
router.register("parent-links", ParentStudentLinkViewSet, basename="parent-link")
router.register("teachers", TeacherViewSet, basename="teacher")
router.register(
    "teacher-qualifications",
    TeacherQualificationViewSet,
    basename="teacher-qualification",
)
router.register(
    "teacher-assignments",
    TeacherSubjectAssignmentViewSet,
    basename="teacher-assignment",
)
router.register(
    "homeroom-assignments",
    HomeroomAssignmentViewSet,
    basename="homeroom-assignment",
)
router.register("attendance", AttendanceViewSet, basename="attendance")
router.register(
    "attendance-reasons",
    AttendanceReasonViewSet,
    basename="attendance-reason",
)
router.register(
    "attendance-summaries",
    AttendanceSummaryViewSet,
    basename="attendance-summary",
)
router.register(
    "intervention-logs",
    InterventionLogViewSet,
    basename="intervention-log",
)
router.register("assessments", AssessmentViewSet, basename="assessment")
router.register(
    "assessment-results",
    AssessmentResultViewSet,
    basename="assessment-result",
)
router.register("announcements", AnnouncementViewSet, basename="announcement")

app_name = "api"
urlpatterns = [
    path(
        "branch-admins/invite/",
        BranchAdminInviteView.as_view(),
        name="branch-admin-invite",
    ),
    path(
        "branch-admins/complete-invitation/",
        BranchAdminCompleteInvitationView.as_view(),
        name="branch-admin-complete-invitation",
    ),
    *router.urls,
    path("", include("media.api.urls")),
]

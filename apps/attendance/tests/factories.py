import factory
import uuid
from factory.django import DjangoModelFactory

from attendance.models import Attendance, AttendanceReason, AttendanceSummary
from organizations.tests.factories import OrganizationFactory
from branches.tests.factories import BranchFactory
from academics.tests.factories import AcademicYearFactory, SectionFactory
from students.tests.factories import StudentFactory
from accounts.tests.factories import UserFactory


class AttendanceFactory(DjangoModelFactory):
    organization = factory.SubFactory(OrganizationFactory)
    branch = factory.SubFactory(BranchFactory)
    academic_year = factory.SubFactory(AcademicYearFactory)
    section = factory.SubFactory(SectionFactory)
    student = factory.SubFactory(StudentFactory)
    recorded_by = factory.SubFactory(UserFactory)
    date = factory.Faker("date_this_year")
    status = Attendance.Status.PRESENT
    remarks = ""
    client_side_id = factory.LazyFunction(uuid.uuid4)

    class Meta:
        model = Attendance


class AttendanceReasonFactory(DjangoModelFactory):
    organization = factory.SubFactory(OrganizationFactory)
    attendance = factory.SubFactory(AttendanceFactory)
    reason_category = AttendanceReason.Category.UNKNOWN
    note = factory.Faker("sentence")
    parent_confirmed = False

    class Meta:
        model = AttendanceReason


class AttendanceSummaryFactory(DjangoModelFactory):
    organization = factory.SubFactory(OrganizationFactory)
    student = factory.SubFactory(StudentFactory)
    academic_year = factory.SubFactory(AcademicYearFactory)
    total_present = 0
    total_absent = 0
    total_late = 0
    total_excused = 0
    total_school_days = 0

    class Meta:
        model = AttendanceSummary

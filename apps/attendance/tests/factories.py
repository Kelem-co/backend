import uuid

import factory
from academics.tests.factories import AcademicYearFactory
from academics.tests.factories import SectionFactory
from accounts.tests.factories import UserFactory
from attendance.models import Attendance
from attendance.models import AttendanceReason
from attendance.models import AttendanceSummary
from branches.tests.factories import BranchFactory
from factory.django import DjangoModelFactory
from organizations.tests.factories import OrganizationFactory
from students.tests.factories import StudentFactory


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

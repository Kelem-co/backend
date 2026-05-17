import factory
from factory.django import DjangoModelFactory
from teachers.models import Teacher, TeacherSubjectAssignment
from accounts.tests.factories import UserFactory
from organizations.tests.factories import OrganizationFactory
from branches.tests.factories import BranchFactory
from academics.tests.factories import SubjectFactory, SectionFactory, AcademicYearFactory


class TeacherFactory(DjangoModelFactory):
    user = factory.SubFactory(UserFactory, role="TEACHER")
    organization = factory.SubFactory(OrganizationFactory)
    branch = factory.SubFactory(BranchFactory)
    employee_id = factory.Sequence(lambda n: f"EMP{n:04d}")
    bio = factory.Faker("text")
    specialization = "Math"
    joining_date = factory.Faker("date_this_decade")

    class Meta:
        model = Teacher

class TeacherSubjectAssignmentFactory(DjangoModelFactory):
    teacher = factory.SubFactory(TeacherFactory)
    organization = factory.SelfAttribute("teacher.organization")
    subject = factory.SubFactory(SubjectFactory)
    section = factory.SubFactory(SectionFactory)
    academic_year = factory.SubFactory(AcademicYearFactory)

    class Meta:
        model = TeacherSubjectAssignment

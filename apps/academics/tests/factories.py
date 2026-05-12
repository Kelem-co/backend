import factory
from factory.django import DjangoModelFactory
from academics.models import AcademicYear, Grade, Section, Subject
from organizations.tests.factories import OrganizationFactory
from branches.tests.factories import BranchFactory

class AcademicYearFactory(DjangoModelFactory):
    organization = factory.SubFactory(OrganizationFactory)
    branch = factory.SubFactory(BranchFactory)
    name = factory.Sequence(lambda n: f"202{n}/202{n+1}")
    start_date = factory.Faker("date_this_year")
    end_date = factory.Faker("date_this_year", after_today=True)
    is_current = False

    class Meta:
        model = AcademicYear

class GradeFactory(DjangoModelFactory):
    organization = factory.SubFactory(OrganizationFactory)
    branch = factory.SubFactory(BranchFactory)
    name = factory.Sequence(lambda n: f"Grade {n}")
    level = factory.Sequence(lambda n: n)

    class Meta:
        model = Grade

class SectionFactory(DjangoModelFactory):
    organization = factory.SubFactory(OrganizationFactory)
    branch = factory.SubFactory(BranchFactory)
    grade = factory.SubFactory(GradeFactory)
    name = factory.Sequence(lambda n: f"Section {chr(65+n % 26)}")

    class Meta:
        model = Section

class SubjectFactory(DjangoModelFactory):
    organization = factory.SubFactory(OrganizationFactory)
    branch = factory.SubFactory(BranchFactory)
    grade = factory.SubFactory(GradeFactory)
    name = factory.Sequence(lambda n: f"Subject {n}")
    code = factory.Sequence(lambda n: f"SUB{n}")

    class Meta:
        model = Subject

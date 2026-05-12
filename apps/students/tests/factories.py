import factory
from factory.django import DjangoModelFactory
from students.models import Student, ParentStudentLink
from organizations.tests.factories import OrganizationFactory
from branches.tests.factories import BranchFactory
from academics.tests.factories import SectionFactory
from accounts.tests.factories import UserFactory

class StudentFactory(DjangoModelFactory):
    organization = factory.SubFactory(OrganizationFactory)
    branch = factory.SubFactory(BranchFactory)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    gender = factory.Iterator(["MALE", "FEMALE"])
    date_of_birth = factory.Faker("date_of_birth", minimum_age=5, maximum_age=18)
    roll_no = factory.Sequence(lambda n: f"STU{n:04d}")
    current_section = factory.SubFactory(SectionFactory)
    admission_date = factory.Faker("date_this_decade")
    status = "ACTIVE"

    class Meta:
        model = Student

class ParentStudentLinkFactory(DjangoModelFactory):
    student = factory.SubFactory(StudentFactory)
    parent = factory.SubFactory(UserFactory)
    relationship_type = factory.Iterator(["FATHER", "MOTHER", "GUARDIAN"])
    is_primary_contact = False

    class Meta:
        model = ParentStudentLink

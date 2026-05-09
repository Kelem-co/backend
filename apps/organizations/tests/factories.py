import factory
from factory import Faker
from factory.django import DjangoModelFactory

from accounts.tests.factories import UserFactory
from organizations.models import Organization


class OrganizationFactory(DjangoModelFactory[Organization]):
    owner = factory.SubFactory(UserFactory)
    name = Faker("company")
    trade_name = Faker("company_suffix")
    license_no = Faker("bban")
    client_full_name = Faker("name")
    business_address = Faker("address")
    business_phone_number = Faker("phone_number")
    client_phone_number = Faker("phone_number")
    status = Organization.Status.ACTIVE

    class Meta:
        model = Organization
        django_get_or_create = ["name"]

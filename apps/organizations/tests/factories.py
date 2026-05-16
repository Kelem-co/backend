import factory
from accounts.tests.factories import UserFactory
from factory import Faker
from factory.django import DjangoModelFactory
from organizations.models import Organization


class OrganizationFactory(DjangoModelFactory[Organization]):
    owner = factory.SubFactory(UserFactory)
    name = Faker("company")
    trade_name = Faker("company_suffix")
    tin_number = Faker("numerify", text="##########")
    license_no = Faker("bban")
    client_full_name = Faker("name")
    business_address = Faker("address")
    business_phone_number = Faker("phone_number")
    client_phone_number = Faker("phone_number")
    status = Organization.Status.ACTIVE
    verification_status = Organization.VerificationStatus.VERIFIED
    verification_failure_reason = ""
    verification_match_source = "license_lookup"
    verified_name = factory.SelfAttribute("name")
    verified_license_no = factory.SelfAttribute("license_no")
    verified_tin_number = factory.SelfAttribute("tin_number")

    class Meta:
        model = Organization
        django_get_or_create = ["name"]

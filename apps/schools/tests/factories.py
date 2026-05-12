from __future__ import annotations

import factory
from factory import Faker
from factory.django import DjangoModelFactory
from organizations.tests.factories import OrganizationFactory
from schools.models import School


class SchoolFactory(DjangoModelFactory[School]):
    organization = factory.SubFactory(OrganizationFactory)
    name = Faker("company")
    description = Faker("paragraph")
    country = Faker("country")
    contact_email = Faker("email")
    contact_phone = Faker("phone_number")
    website = Faker("url")
    status = School.Status.ACTIVE

    class Meta:
        model = School
        django_get_or_create = ["name"]

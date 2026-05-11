from __future__ import annotations

import factory
from factory import Faker
from factory.django import DjangoModelFactory

from accounts.tests.factories import UserFactory
from schools.tests.factories import SchoolFactory
from branches.models import Branch, BranchAdmin


class BranchFactory(DjangoModelFactory[Branch]):
    organization = factory.SelfAttribute("school.organization")
    school = factory.SubFactory(SchoolFactory)
    name = Faker("city")
    address = Faker("address")
    city = Faker("city")
    region = Faker("state")
    contact_phone = Faker("phone_number")
    contact_email = Faker("email")
    status = Branch.Status.ACTIVE

    class Meta:
        model = Branch
        django_get_or_create = ["name", "school"]


class BranchAdminFactory(DjangoModelFactory[BranchAdmin]):
    organization = factory.SelfAttribute("branch.organization")
    branch = factory.SubFactory(BranchFactory)
    user = factory.SubFactory(UserFactory)
    emergency_contact_name = Faker("name")
    emergency_contact_phone = Faker("phone_number")
    role_title = "Admin"
    qualification = "Certified Administrator"
    status = BranchAdmin.Status.ACTIVE

    class Meta:
        model = BranchAdmin
        django_get_or_create = ["user", "branch"]

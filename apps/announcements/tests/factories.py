import factory
from announcements.models import Announcement
from branches.tests.factories import BranchFactory
from factory.django import DjangoModelFactory
from organizations.tests.factories import OrganizationFactory


class AnnouncementFactory(DjangoModelFactory):
    organization = factory.SubFactory(OrganizationFactory)
    branch = factory.SubFactory(BranchFactory)
    subject = factory.Sequence(lambda n: f"Announcement {n}")
    message = factory.Faker("text")
    is_urgent = False
    status = Announcement.StatusChoices.DRAFT
    target_roles = Announcement.TargetRoleChoices.BOTH

    class Meta:
        model = Announcement

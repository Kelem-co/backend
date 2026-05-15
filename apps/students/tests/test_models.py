import pytest
from academics.tests.factories import GradeFactory
from academics.tests.factories import SectionFactory
from branches.tests.factories import BranchFactory
from django.core.exceptions import ValidationError
from organizations.tests.factories import OrganizationFactory
from students.models import ParentStudentLink
from students.tests.factories import ParentFactory
from students.tests.factories import StudentFactory


@pytest.mark.django_db
def test_parent_can_belong_to_multiple_organizations_and_branches():
    expected_count = 2
    parent = ParentFactory()
    first_branch = parent.branches.first()
    first_organization = parent.organizations.first()

    second_organization = OrganizationFactory()
    second_branch = BranchFactory(school__organization=second_organization)
    second_grade = GradeFactory(
        organization=second_organization,
        branch=second_branch,
    )
    second_section = SectionFactory(
        organization=second_organization,
        branch=second_branch,
        grade=second_grade,
    )
    second_student = StudentFactory(
        organization=second_organization,
        branch=second_branch,
        current_section=second_section,
    )
    parent.organizations.add(second_student.organization)
    parent.branches.add(second_student.branch)

    parent.full_clean()

    assert parent.organizations.count() == expected_count
    assert parent.branches.count() == expected_count
    assert first_branch in parent.branches.all()
    assert first_organization in parent.organizations.all()


@pytest.mark.django_db
def test_parent_rejects_branch_outside_selected_organizations():
    parent = ParentFactory()
    invalid_student = StudentFactory()
    parent.branches.add(invalid_student.branch)

    with pytest.raises(ValidationError):
        parent.full_clean()


@pytest.mark.django_db
def test_parent_student_link_rejects_mismatched_membership():
    student = StudentFactory()
    mismatched_parent = ParentFactory()
    link = ParentStudentLink(student=student, parent=mismatched_parent)

    with pytest.raises(ValidationError):
        link.full_clean()

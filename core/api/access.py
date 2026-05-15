from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from branches.models import Branch
from branches.models import BranchAdmin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db.models import QuerySet

if TYPE_CHECKING:
    from students.models import Parent
    from students.models import Student


def get_branch_admin_branch_ids(user: Any) -> list[str]:
    if not getattr(user, "is_authenticated", False):
        return []

    return [
        str(branch_id)
        for branch_id in BranchAdmin.objects.filter(
            user=user,
            status=BranchAdmin.Status.ACTIVE,
        ).values_list("branch_id", flat=True)
    ]


def get_parent_branch_ids(user: Any) -> list[str]:
    if not getattr(user, "is_authenticated", False):
        return []

    try:
        parent_profile = user.parent_profile
    except ObjectDoesNotExist:
        return []

    return [
        str(branch_id)
        for branch_id in parent_profile.branches.values_list("id", flat=True)
    ]


def get_parent_organization_ids(user: Any) -> list[str]:
    if not getattr(user, "is_authenticated", False):
        return []

    try:
        parent_profile = user.parent_profile
    except ObjectDoesNotExist:
        return []

    return [
        str(organization_id)
        for organization_id in parent_profile.organizations.values_list("id", flat=True)
    ]


def scope_queryset_for_user(
    queryset: QuerySet,
    user: Any,
    *,
    organization_lookup: str = "organization",
    branch_lookup: str | None = "branch",
) -> QuerySet:
    return queryset.filter(
        user_resource_access_filter(
            user,
            organization_lookup=organization_lookup,
            branch_lookup=branch_lookup,
        ),
    ).distinct()


def user_resource_access_filter(
    user: Any,
    *,
    organization_lookup: str = "organization",
    branch_lookup: str | None = "branch",
) -> Q:
    if not user.is_authenticated:
        return Q(pk__in=[])

    if user.is_superuser:
        return Q()

    filters = [
        Q(**{f"{organization_lookup}__owner": user}),
    ]

    parent_organization_ids = get_parent_organization_ids(user)
    if parent_organization_ids:
        organization_id_lookup = (
            f"{organization_lookup}__id__in"
            if organization_lookup.rsplit("__", maxsplit=1)[-1] == "organizations"
            else f"{organization_lookup}_id__in"
        )
        filters.append(Q(**{organization_id_lookup: parent_organization_ids}))

    branch_ids = get_branch_admin_branch_ids(user)
    parent_branch_ids = get_parent_branch_ids(user)
    branch_ids = [*branch_ids, *parent_branch_ids]

    if branch_lookup is not None and branch_ids:
        if branch_lookup == "self":
            lookup = "id__in"
        elif branch_lookup.split("__")[-1] == "branches":
            lookup = f"{branch_lookup}__id__in"
        else:
            lookup = f"{branch_lookup}_id__in"
        filters.append(Q(**{lookup: branch_ids}))

    q = Q()
    for f in filters:
        q |= f

    return q


def user_can_access_branch(user: Any, branch: Branch) -> bool:
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return (
        branch.organization.owner_id == user.id
        or BranchAdmin.objects.filter(
            user=user,
            branch=branch,
            status=BranchAdmin.Status.ACTIVE,
        ).exists()
    )


def user_can_access_student(user: Any, student: Student) -> bool:
    return user_can_access_branch(user, student.branch)


def user_can_access_student_as_parent_or_staff(user: Any, student: Student) -> bool:
    if user_can_access_student(user, student):
        return True

    return student.parent_links.filter(parent__user=user).exists()


def user_can_access_parent(user: Any, parent: Parent) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False

    if user.is_superuser:
        return True

    if parent.user_id == user.id:
        return True

    if parent.organizations.filter(owner=user).exists():
        return True

    branch_ids = get_branch_admin_branch_ids(user)
    return bool(branch_ids and parent.branches.filter(id__in=branch_ids).exists())

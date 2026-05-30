from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import Q
from students.models import ParentStudentLink
from teachers.models import Teacher

if TYPE_CHECKING:
    from messaging.models import ChatThread


def user_can_access_thread(user, thread: ChatThread) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False

    participant_ids = {thread.parent.user_id, thread.teacher.user_id}
    return user.id in participant_ids


def is_teacher_assigned_to_student(teacher: Teacher, student_id: str) -> bool:
    if teacher.subject_assignments.filter(section__students__id=student_id).exists():
        return True

    return teacher.homeroom_assignments.filter(
        section__students__id=student_id,
    ).exists()


def can_create_thread(parent_id: str, teacher_id: str, student_id: str) -> bool:
    parent_student_ok = ParentStudentLink.objects.filter(
        parent_id=parent_id,
        student_id=student_id,
    ).exists()
    if not parent_student_ok:
        return False

    try:
        teacher = Teacher.objects.get(id=teacher_id)
    except Teacher.DoesNotExist:
        return False

    return is_teacher_assigned_to_student(teacher, student_id)


def thread_scope_filter_for_user(user):
    if not getattr(user, "is_authenticated", False):
        return Q(pk__in=[])
    return Q(parent__user=user) | Q(teacher__user=user)

from academics.tests.factories import AcademicYearFactory
from academics.tests.factories import SectionFactory
from academics.tests.factories import SubjectFactory
from messaging.models import MessageRead
from messaging.tests.factories import ChatThreadFactory
from messaging.tests.factories import TeacherFactory
from rest_framework import status
from rest_framework.test import APIClient
from students.models import ParentStudentLink
from students.tests.factories import ParentFactory
from students.tests.factories import StudentFactory
from teachers.models import TeacherSubjectAssignment

from media.models import MediaFile
from media.models import StatusChoices


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _assign_teacher_to_student_section(teacher, student):
    section = student.current_section or SectionFactory(
        organization=student.organization,
        branch=student.branch,
    )
    if student.current_section_id is None:
        student.current_section = section
        student.save(update_fields=["current_section", "updated_at"])

    ay = AcademicYearFactory(
        organization=student.organization,
        branch=student.branch,
        is_current=True,
    )
    subject = section.grade.subjects.first() or SubjectFactory(
        organization=student.organization,
        branch=student.branch,
        grade=section.grade,
        name="Math",
        code="MTH101",
    )

    TeacherSubjectAssignment.objects.create(
        teacher=teacher,
        organization=student.organization,
        subject=subject,
        section=section,
        academic_year=ay,
    )


def test_create_thread_and_message_and_mark_read(db):
    student = StudentFactory()
    parent = ParentFactory()
    parent.organizations.add(student.organization)
    parent.branches.add(student.branch)
    ParentStudentLink.objects.create(
        parent=parent,
        student=student,
        relationship_type="MOTHER",
    )

    teacher = TeacherFactory(_student=student)
    _assign_teacher_to_student_section(teacher, student)

    parent_client = _client(parent.user)
    thread_resp = parent_client.post(
        "/api/chat-threads/",
        {
            "parent": str(parent.id),
            "teacher": str(teacher.id),
            "student": str(student.id),
        },
        format="json",
    )
    assert thread_resp.status_code == status.HTTP_201_CREATED
    thread_id = thread_resp.data["id"]

    msg_resp = parent_client.post(
        f"/api/chat-threads/{thread_id}/messages/",
        {"text": "Hello teacher"},
        format="json",
    )
    assert msg_resp.status_code == status.HTTP_201_CREATED

    teacher_client = _client(teacher.user)
    read_resp = teacher_client.post(
        f"/api/chat-threads/{thread_id}/mark-read/",
        {},
        format="json",
    )
    assert read_resp.status_code == status.HTTP_200_OK
    assert read_resp.data["count"] == 1

    message_id = msg_resp.data["id"]
    assert MessageRead.objects.filter(
        message_id=message_id,
        reader=teacher.user,
    ).exists()


def test_reject_invalid_attachment_or_access(db):
    thread = ChatThreadFactory()
    client = _client(thread.parent.user)

    media = MediaFile.objects.create(
        key="media/a/b/file.pdf",
        bucket="test",
        file_name="file.pdf",
        content_type="application/pdf",
        status=StatusChoices.PENDING,
        uploaded_by=thread.parent.user,
    )

    resp = client.post(
        f"/api/chat-threads/{thread.id}/messages/",
        {"attachment": str(media.id)},
        format="json",
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_non_participant_forbidden(db):
    thread = ChatThreadFactory()
    outsider = ParentFactory()
    outsider_client = _client(outsider.user)

    resp = outsider_client.get(f"/api/chat-threads/{thread.id}/")
    assert resp.status_code == status.HTTP_404_NOT_FOUND

    resp = outsider_client.post(
        f"/api/chat-threads/{thread.id}/messages/",
        {"text": "x"},
        format="json",
    )
    assert resp.status_code in {
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    }

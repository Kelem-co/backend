# ruff: noqa: SLF001
import factory
from accounts.tests.factories import UserFactory
from factory.django import DjangoModelFactory
from messaging.models import ChatMessage
from messaging.models import ChatThread
from students.tests.factories import ParentFactory
from students.tests.factories import ParentStudentLinkFactory
from students.tests.factories import StudentFactory
from teachers.models import Teacher


class TeacherFactory(DjangoModelFactory):
    user = factory.SubFactory(UserFactory, role="TEACHER")
    _student = factory.SubFactory(StudentFactory)
    organization = factory.LazyAttribute(lambda o: o._student.organization)
    branch = factory.LazyAttribute(lambda o: o._student.branch)
    employee_id = factory.Sequence(lambda n: f"EMP-{n}")

    class Meta:
        model = Teacher
        exclude = ("_student",)


class ChatThreadFactory(DjangoModelFactory):
    student = factory.SubFactory(StudentFactory)
    parent = factory.SubFactory(ParentFactory)
    teacher = factory.SubFactory(
        TeacherFactory,
        _student=factory.SelfAttribute("..student"),
    )
    organization = factory.SelfAttribute("student.organization")
    branch = factory.SelfAttribute("student.branch")

    class Meta:
        model = ChatThread

    @factory.post_generation
    def link_parent(self, create, extracted, **kwargs):
        del extracted, kwargs
        if not create:
            return
        ParentStudentLinkFactory(parent=self.parent, student=self.student)


class ChatMessageFactory(DjangoModelFactory):
    thread = factory.SubFactory(ChatThreadFactory)
    sender = factory.SelfAttribute("thread.parent.user")
    text = factory.Faker("sentence")

    class Meta:
        model = ChatMessage

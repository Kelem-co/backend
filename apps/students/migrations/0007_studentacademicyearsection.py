import django.db.models.deletion
import uuid

from django.db import migrations
from django.db import models


def backfill_student_academic_year_sections(apps, schema_editor):
    AcademicYear = apps.get_model("academics", "AcademicYear")
    Student = apps.get_model("students", "Student")
    StudentAcademicYearSection = apps.get_model(
        "students",
        "StudentAcademicYearSection",
    )

    current_academic_years = {
        academic_year.branch_id: academic_year
        for academic_year in AcademicYear.objects.filter(is_current=True)
    }

    for student in Student.objects.select_related(
        "current_section__academic_year",
    ).iterator():
        if student.current_section_id is not None:
            academic_year = student.current_section.academic_year
            section = student.current_section
        else:
            academic_year = current_academic_years.get(student.branch_id)
            section = None

        if academic_year is None:
            continue

        StudentAcademicYearSection.objects.update_or_create(
            student_id=student.id,
            academic_year_id=academic_year.id,
            defaults={"section_id": section.id if section is not None else None},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("academics", "0004_gradesubject"),
        ("students", "0006_alter_student_roll_no"),
    ]

    operations = [
        migrations.CreateModel(
            name="StudentAcademicYearSection",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Updated At"),
                ),
                (
                    "academic_year",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="student_sections",
                        to="academics.academicyear",
                        verbose_name="Academic Year",
                    ),
                ),
                (
                    "section",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="student_academic_year_sections",
                        to="academics.section",
                        verbose_name="Section",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="academic_year_sections",
                        to="students.student",
                        verbose_name="Student",
                    ),
                ),
            ],
            options={
                "verbose_name": "Student Academic Year Section",
                "verbose_name_plural": "Student Academic Year Sections",
                "ordering": ["-created_at"],
                "unique_together": {("student", "academic_year")},
            },
        ),
        migrations.RunPython(
            backfill_student_academic_year_sections,
            migrations.RunPython.noop,
        ),
    ]

import uuid

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("academics", "0004_gradesubject"),
        ("media", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CalendarDocument",
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
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Updated At")),
                (
                    "academic_year",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.CASCADE,
                        related_name="calendar_documents",
                        to="academics.academicyear",
                        verbose_name="Academic Year",
                    ),
                ),
                (
                    "branch",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="calendar_documents",
                        to="branches.branch",
                        verbose_name="Branch",
                    ),
                ),
                (
                    "media_file",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="calendar_documents",
                        to="media.mediafile",
                        verbose_name="Media File",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="calendar_documents",
                        to="organizations.organization",
                        verbose_name="Organization",
                    ),
                ),
            ],
            options={
                "verbose_name": "Calendar Document",
                "verbose_name_plural": "Calendar Documents",
                "ordering": ["-created_at"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("organization", "branch", "academic_year"),
                        name="unique_calendar_document_per_scope",
                    ),
                ],
            },
        ),
    ]

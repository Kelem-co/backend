import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations
from django.db import models


def migrate_parent_profiles(apps, schema_editor):
    Parent = apps.get_model("students", "Parent")
    ParentStudentLink = apps.get_model("students", "ParentStudentLink")
    User = apps.get_model("accounts", "User")

    for link in ParentStudentLink.objects.select_related("student", "parent"):
        parent_profile, _created = Parent.objects.get_or_create(
            user_id=link.parent_id,
            defaults={
                "secondary_phone_number": "",
                "occupation": "",
                "work_address": "",
                "relationship_notes": "",
                "emergency_contact_name": "",
                "emergency_contact_phone": "",
                "is_active": True,
            },
        )
        parent_profile.organizations.add(link.student.organization_id)
        parent_profile.branches.add(link.student.branch_id)
        link.parent_profile_id = parent_profile.id
        link.save(update_fields=["parent_profile"])

        user = User.objects.get(id=link.parent_id)
        if user.role != "PARENT":
            user.role = "PARENT"
            user.save(update_fields=["role"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_user_role"),
        ("branches", "0001_initial"),
        ("organizations", "0002_organization_tin_number"),
        ("students", "0002_alter_student_unique_together"),
    ]

    operations = [
        migrations.CreateModel(
            name="Parent",
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
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Created At",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="Updated At",
                    ),
                ),
                (
                    "secondary_phone_number",
                    models.CharField(
                        blank=True,
                        max_length=20,
                        verbose_name="Secondary Phone Number",
                    ),
                ),
                (
                    "occupation",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="Occupation",
                    ),
                ),
                (
                    "work_address",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="Work Address",
                    ),
                ),
                (
                    "relationship_notes",
                    models.TextField(
                        blank=True,
                        verbose_name="Relationship Notes",
                    ),
                ),
                (
                    "emergency_contact_name",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="Emergency Contact Name",
                    ),
                ),
                (
                    "emergency_contact_phone",
                    models.CharField(
                        blank=True,
                        max_length=50,
                        verbose_name="Emergency Contact Phone",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        verbose_name="Is Active",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parent_profile",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "Parent",
                "verbose_name_plural": "Parents",
                "ordering": ["user__name", "user__email"],
            },
        ),
        migrations.AddField(
            model_name="parent",
            name="branches",
            field=models.ManyToManyField(
                blank=True,
                related_name="parents",
                to="branches.branch",
                verbose_name="Branches",
            ),
        ),
        migrations.AddField(
            model_name="parent",
            name="organizations",
            field=models.ManyToManyField(
                blank=True,
                related_name="parents",
                to="organizations.organization",
                verbose_name="Organizations",
            ),
        ),
        migrations.AddField(
            model_name="parentstudentlink",
            name="parent_profile",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="student_links",
                to="students.parent",
                verbose_name="Parent",
            ),
        ),
        migrations.RunPython(
            migrate_parent_profiles,
            migrations.RunPython.noop,
        ),
        migrations.AlterUniqueTogether(
            name="parentstudentlink",
            unique_together={("student", "parent_profile")},
        ),
        migrations.RemoveField(
            model_name="parentstudentlink",
            name="parent",
        ),
        migrations.RenameField(
            model_name="parentstudentlink",
            old_name="parent_profile",
            new_name="parent",
        ),
        migrations.AlterField(
            model_name="parentstudentlink",
            name="parent",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="student_links",
                to="students.parent",
                verbose_name="Parent",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="parentstudentlink",
            unique_together={("student", "parent")},
        ),
    ]

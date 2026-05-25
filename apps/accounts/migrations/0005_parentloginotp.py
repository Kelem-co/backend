import uuid

import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_approvallogintoken"),
    ]

    operations = [
        migrations.CreateModel(
            name="ParentLoginOTP",
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
                ("phone_number", models.CharField(max_length=20, verbose_name="Phone Number")),
                ("code_hash", models.CharField(max_length=64, verbose_name="Code Hash")),
                ("expires_at", models.DateTimeField(verbose_name="Expires At")),
                ("used_at", models.DateTimeField(blank=True, null=True, verbose_name="Used At")),
                (
                    "failed_attempts",
                    models.PositiveSmallIntegerField(default=0, verbose_name="Failed Attempts"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parent_login_otps",
                        to="accounts.user",
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "Parent Login OTP",
                "verbose_name_plural": "Parent Login OTPs",
                "ordering": ["-created_at"],
            },
        ),
    ]

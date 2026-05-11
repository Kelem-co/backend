import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("media", "0001_initial"),
        ("organizations", "0003_organization_verification_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="organization",
            name="business_license_image",
        ),
        migrations.AddField(
            model_name="organization",
            name="business_license_image",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="organization_license_files",
                to="media.mediafile",
                verbose_name="Business License Image",
            ),
        ),
    ]

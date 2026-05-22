import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("announcements", "0001_initial"),
        ("media", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="announcement",
            name="attachment",
        ),
        migrations.AddField(
            model_name="announcement",
            name="attachment",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="announcement_attachments",
                to="media.mediafile",
                verbose_name="Attachment",
            ),
        ),
    ]

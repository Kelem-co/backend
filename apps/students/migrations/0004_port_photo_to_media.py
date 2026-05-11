import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("media", "0001_initial"),
        ("students", "0003_parent_parentstudentlink_parent_profile"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="student",
            name="photo",
        ),
        migrations.AddField(
            model_name="student",
            name="photo",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="student_photo_files",
                to="media.mediafile",
                verbose_name="Photo",
            ),
        ),
    ]

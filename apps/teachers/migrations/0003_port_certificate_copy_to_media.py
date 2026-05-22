import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("media", "0001_initial"),
        ("teachers", "0002_homeroomassignment"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="teacherqualification",
            name="certificate_copy",
        ),
        migrations.AddField(
            model_name="teacherqualification",
            name="certificate_copy",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="teacher_qualification_certificate_files",
                to="media.mediafile",
                verbose_name="Certificate Copy",
            ),
        ),
    ]

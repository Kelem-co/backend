from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("academics", "0004_gradesubject"),
        ("core", "0004_port_importjob_file_to_media"),
    ]

    operations = [
        migrations.AddField(
            model_name="importjob",
            name="current_section",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name="import_jobs",
                to="academics.section",
            ),
        ),
    ]

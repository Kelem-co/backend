import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("media", "0001_initial"),
        ("core", "0003_alter_importjob_task_id"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="importjob",
            name="file",
        ),
        migrations.AddField(
            model_name="importjob",
            name="file",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="import_jobs",
                to="media.mediafile",
                verbose_name="Uploaded File",
            ),
        ),
    ]

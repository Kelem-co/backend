import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("media", "0001_initial"),
        ("schools", "0003_school_description"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="school",
            name="logo",
        ),
        migrations.AddField(
            model_name="school",
            name="logo",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="school_logo_files",
                to="media.mediafile",
                verbose_name="Logo",
            ),
        ),
    ]

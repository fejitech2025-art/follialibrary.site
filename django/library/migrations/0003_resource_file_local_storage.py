from django.core.files.storage import FileSystemStorage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0002_alter_resource_cover"),
    ]

    operations = [
        migrations.AlterField(
            model_name="resource",
            name="file",
            field=models.FileField(
                blank=True,
                storage=FileSystemStorage(),
                upload_to="resources/",
            ),
        ),
    ]

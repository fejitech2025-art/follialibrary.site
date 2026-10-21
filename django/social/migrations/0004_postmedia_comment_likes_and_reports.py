import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("library", "0004_resourcecomment_parent"),
        ("social", "0003_postcomment_parent"),
    ]

    operations = [
        migrations.CreateModel(
            name="PostMedia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="posts/")),
                ("media_type", models.CharField(choices=[("image", "Image"), ("video", "Video")], default="image", max_length=12)),
                ("position", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="media_items", to="social.post")),
            ],
            options={"ordering": ["position", "id"]},
        ),
        migrations.CreateModel(
            name="PostCommentLike",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("comment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="likes", to="social.postcomment")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={"constraints": [models.UniqueConstraint(fields=("user", "comment"), name="unique_post_comment_like")]},
        ),
        migrations.AddField(
            model_name="contentreport",
            name="post_comment",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="reports", to="social.postcomment"),
        ),
        migrations.AddField(
            model_name="contentreport",
            name="resource",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="reports", to="library.resource"),
        ),
        migrations.AddField(
            model_name="contentreport",
            name="resource_comment",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="reports", to="library.resourcecomment"),
        ),
        migrations.AddField(
            model_name="contentreport",
            name="status",
            field=models.CharField(choices=[("pending", "Pending"), ("reviewed", "Reviewed"), ("resolved", "Resolved")], default="pending", max_length=16),
        ),
        migrations.AlterField(
            model_name="contentreport",
            name="reason",
            field=models.CharField(choices=[("spam", "Spam"), ("harassment", "Harassment"), ("inappropriate", "Inappropriate content"), ("impersonation", "Impersonation"), ("other", "Other")], default="other", max_length=80),
        ),
    ]

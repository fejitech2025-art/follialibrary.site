from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_pushsubscription_notification_event_key_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="comment_id",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="notification",
            name="type",
            field=models.CharField(choices=[("follow", "Follow"), ("like", "Like"), ("comment", "Comment"), ("comment_reply", "Comment reply"), ("comment_like", "Comment like"), ("book_club_join", "Book Club activity"), ("book_club_reply", "Book Club reply"), ("book_club_admin", "Book Club role")], max_length=32),
        ),
    ]

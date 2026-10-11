from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify

from .models import Profile

User = get_user_model()


@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    if not created:
        return
    base = slugify(instance.username)[:24] or f"reader-{instance.pk}"
    username = base
    suffix = 1
    while Profile.objects.filter(username=username).exists():
        suffix += 1
        username = f"{base[:24]}-{suffix}"
    Profile.objects.get_or_create(
        user=instance,
        defaults={"username": username, "display_name": instance.get_full_name()},
    )

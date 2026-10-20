from urllib.parse import urlsplit

from botocore.exceptions import BotoCoreError
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from storages.backends.s3 import S3Storage


class R2MediaStorage(S3Storage):
    """The one backend used by public image and video model fields."""

    def __init__(self, **kwargs):
        if not settings.R2_STORAGE_CONFIGURED:
            raise ImproperlyConfigured(
                "Cloudflare R2 media storage is not configured. Set the "
                "R2 bucket, endpoint, access key ID, and secret access key."
            )

        # django-storages expects custom_domain to be a hostname, not a URL.
        public_domain = settings.R2_PUBLIC_DOMAIN or None
        options = {
            "bucket_name": settings.R2_BUCKET_NAME,
            "endpoint_url": settings.R2_ENDPOINT_URL,
            "access_key": settings.R2_ACCESS_KEY_ID,
            "secret_key": settings.R2_SECRET_ACCESS_KEY,
            "region_name": settings.R2_REGION,
            "custom_domain": public_domain,
            "querystring_auth": not bool(public_domain),
            "default_acl": None,
            "file_overwrite": False,
            "addressing_style": "path",
            "signature_version": "s3v4",
        }
        options.update(kwargs)
        super().__init__(**options)


def media_storage_available_for_upload():
    """Whether upload views can save media without falling back in production."""
    return settings.R2_STORAGE_CONFIGURED or settings.DEBUG


def storage_file_url(file_field, request=None):
    """Return a usable URL, keeping list/profile serialization resilient."""
    if not file_field:
        return ""

    try:
        url = file_field.url
    except (ImproperlyConfigured, BotoCoreError, OSError, ValueError):
        return ""

    if not url:
        return ""
    if request and not urlsplit(url).scheme:
        if url.startswith("//"):
            return f"{request.scheme}:{url}"
        return request.build_absolute_uri(url)
    return url

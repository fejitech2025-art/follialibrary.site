
from django.conf import settings
from storages.backends.s3 import S3Storage


class R2MediaStorage(S3Storage):
    bucket_name = settings.R2_BUCKET_NAME
    endpoint_url = settings.R2_ENDPOINT_URL
    access_key = settings.R2_ACCESS_KEY_ID
    secret_key = settings.R2_SECRET_ACCESS_KEY
    region_name = settings.R2_REGION

    default_acl = None
    file_overwrite = False
    querystring_auth = True

from rest_framework import serializers

from config.storage_backends import storage_file_url


class SafeStorageFileField(serializers.FileField):
    """Keep uploads writable while serializing unavailable media as null."""

    def to_representation(self, value):
        url = storage_file_url(value, self.context.get("request"))
        return url or None

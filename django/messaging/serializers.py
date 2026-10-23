from rest_framework import serializers

from config.storage_backends import storage_file_url
from social.models import Post
from .models import DirectMessage


class DirectMessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(read_only=True)
    attachment_url = serializers.SerializerMethodField()
    shared_post_preview = serializers.SerializerMethodField()
    pending = serializers.SerializerMethodField()

    class Meta:
        model = DirectMessage
        fields = ["id", "client_id", "conversation_id", "sender_id", "message_type", "body",
                  "attachment_url", "duration_seconds", "shared_post_preview", "read_at", "created_at", "pending"]

    def get_attachment_url(self, obj):
        if not obj.attachment:
            return ""
        request = self.context.get("request")
        path = f"/api/messages/{obj.pk}/media/"
        return request.build_absolute_uri(path) if request else path

    def get_pending(self, obj):
        return False

    def get_shared_post_preview(self, obj):
        post = obj.shared_post
        if not post:
            return None
        author = getattr(post.author, "profile", None)
        media = post.media_items.first()
        field = media.file if media else post.media
        request = self.context.get("request")
        return {
            "id": post.pk,
            "author": (author.display_name or author.username) if author else post.author.username,
            "excerpt": post.body[:180],
            "media_url": storage_file_url(field, request) if field else "",
            "url": f"/post/{post.pk}",
        }


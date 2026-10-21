from rest_framework import serializers

from accounts.serializers import ProfileSerializer
from config.serializer_fields import SafeStorageFileField
from config.storage_backends import storage_file_url
from .models import Post, PostComment


class PostSerializer(serializers.ModelSerializer):
    author = ProfileSerializer(source="author.profile", read_only=True)
    author_id = serializers.IntegerField(read_only=True)
    media = SafeStorageFileField(required=False, allow_null=True)
    media_url = serializers.SerializerMethodField()
    media_items = serializers.SerializerMethodField()
    media_download_url = serializers.SerializerMethodField()
    like_count = serializers.IntegerField(source="likes.count", read_only=True)
    comment_count = serializers.IntegerField(source="comments.count", read_only=True)
    liked = serializers.SerializerMethodField()
    saved = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ["id", "author_id", "author", "body", "media", "media_url", "media_type", "media_items", "media_download_url", "created_at", "updated_at", "like_count", "comment_count", "liked", "saved", "is_owner"]
        read_only_fields = ["id", "author_id", "author", "media_url", "media_items", "media_download_url", "created_at", "updated_at", "like_count", "comment_count", "liked", "saved", "is_owner"]

    def get_media_url(self, obj):
        item = obj.media_items.first()
        if item:
            return storage_file_url(item.file, self.context.get("request"))
        return storage_file_url(obj.media, self.context.get("request"))

    def get_media_items(self, obj):
        request = self.context.get("request")
        items = list(obj.media_items.all())
        if not items and obj.media:
            path = f"/api/posts/{obj.pk}/file/"
            return [{
                "id": None,
                "media_type": obj.media_type,
                "url": storage_file_url(obj.media, request),
                "download_url": request.build_absolute_uri(path) if request else path,
            }]
        return [{
            "id": item.pk,
            "media_type": item.media_type,
            "url": storage_file_url(item.file, request),
            "download_url": request.build_absolute_uri(f"/api/posts/{obj.pk}/media/{item.pk}/file/") if request else f"/api/posts/{obj.pk}/media/{item.pk}/file/",
        } for item in items]

    def get_media_download_url(self, obj):
        if not obj.media and not obj.media_items.exists():
            return ""
        request = self.context.get("request")
        path = f"/api/posts/{obj.pk}/file/"
        return request.build_absolute_uri(path) if request else path

    def get_liked(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.likes.filter(user=request.user).exists())

    def get_saved(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.bookmarks.filter(user=request.user).exists())

    def get_is_owner(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.author_id == request.user.pk)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Keep legacy clients on the protected download route. `media_url` and
        # `media_items[].url` remain the original preview sources.
        if data.get("media_download_url"):
            data["media"] = data["media_download_url"]
        return data


class PostCommentSerializer(serializers.ModelSerializer):
    profiles = ProfileSerializer(source="user.profile", read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    parent_id = serializers.IntegerField(read_only=True)
    replies = serializers.SerializerMethodField()
    like_count = serializers.IntegerField(source="likes.count", read_only=True)
    liked = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = ["id", "post_id", "user_id", "parent_id", "content", "created_at", "profiles", "replies", "like_count", "liked"]
        read_only_fields = ["id", "post_id", "user_id", "parent_id", "created_at", "profiles", "replies", "like_count", "liked"]

    def get_liked(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.likes.filter(user=request.user).exists())

    def validate_content(self, value):
        content = value.strip()
        if not content:
            raise serializers.ValidationError("Comment cannot be empty.")
        return content

    def get_replies(self, obj):
        replies = obj.replies.select_related("user__profile").order_by("created_at")[:100]
        return PostCommentReplySerializer(replies, many=True, context=self.context).data


class PostCommentReplySerializer(serializers.ModelSerializer):
    profiles = ProfileSerializer(source="user.profile", read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    parent_id = serializers.IntegerField(read_only=True)
    like_count = serializers.IntegerField(source="likes.count", read_only=True)
    liked = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = ["id", "post_id", "user_id", "parent_id", "content", "created_at", "profiles", "like_count", "liked"]

    def get_liked(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.likes.filter(user=request.user).exists())

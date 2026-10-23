from django.urls import reverse
from rest_framework import serializers

from accounts.serializers import ProfileSerializer
from config.serializer_fields import SafeStorageFileField
from config.storage_backends import storage_file_url
from .models import Resource, ResourceComment


class ResourceSerializer(serializers.ModelSerializer):
    profiles = ProfileSerializer(source="author.profile", read_only=True)
    author_id = serializers.IntegerField(read_only=True)
    cover = SafeStorageFileField(required=False, allow_null=True)
    file = SafeStorageFileField(required=False, allow_null=True)
    cover_url = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    like_count = serializers.IntegerField(source="likes.count", read_only=True)
    comment_count = serializers.IntegerField(source="comments.count", read_only=True)
    liked = serializers.SerializerMethodField()
    saved = serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = ["id", "author_id", "title", "description", "category", "language", "tags", "cover", "cover_url", "file", "file_url", "file_name", "file_type", "is_free", "price", "status", "created_at", "like_count", "comment_count", "liked", "saved", "profiles"]
        read_only_fields = ["id", "author_id", "created_at", "cover_url", "file_url", "profiles", "like_count", "comment_count", "liked", "saved"]

    def get_cover_url(self, obj):
        return storage_file_url(obj.cover, self.context.get("request"))

    def get_file_url(self, obj):
        request = self.context.get("request")
        if not obj.file:
            return ""
        url = reverse("resource-file", kwargs={"resource_id": obj.pk})
        return request.build_absolute_uri(url) if request else url

    def get_liked(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.likes.filter(user=request.user).exists())

    def get_saved(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.bookmarks.filter(user=request.user).exists())

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Keep storage URLs private; `file` and `file_url` use the access-checked
        # download view. Previews use the separate route.
        data["file"] = data.get("file_url") or None
        return data


class ResourceCommentSerializer(serializers.ModelSerializer):
    profiles = ProfileSerializer(source="user.profile", read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    parent_id = serializers.IntegerField(read_only=True)
    replies = serializers.SerializerMethodField()
    like_count = serializers.IntegerField(source="likes.count", read_only=True)
    liked = serializers.SerializerMethodField()

    class Meta:
        model = ResourceComment
        fields = ["id", "user_id", "resource_id", "parent_id", "content", "created_at", "profiles", "replies", "like_count", "liked"]
        read_only_fields = ["id", "user_id", "resource_id", "parent_id", "created_at", "profiles", "replies", "like_count", "liked"]

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
        return ResourceCommentReplySerializer(replies, many=True, context=self.context).data


class ResourceCommentReplySerializer(serializers.ModelSerializer):
    profiles = ProfileSerializer(source="user.profile", read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    parent_id = serializers.IntegerField(read_only=True)
    like_count = serializers.IntegerField(source="likes.count", read_only=True)
    liked = serializers.SerializerMethodField()

    class Meta:
        model = ResourceComment
        fields = ["id", "user_id", "resource_id", "parent_id", "content", "created_at", "profiles", "like_count", "liked"]

    def get_liked(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.likes.filter(user=request.user).exists())

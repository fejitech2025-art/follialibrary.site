from django.urls import reverse
from rest_framework import serializers

from accounts.serializers import ProfileSerializer
from .models import Resource, ResourceComment


class ResourceSerializer(serializers.ModelSerializer):
    profiles = ProfileSerializer(source="author.profile", read_only=True)
    author_id = serializers.IntegerField(read_only=True)
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
        request = self.context.get("request")
        return request.build_absolute_uri(obj.cover.url) if obj.cover and request else (obj.cover.url if obj.cover else "")

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


class ResourceCommentSerializer(serializers.ModelSerializer):
    profiles = ProfileSerializer(source="user.profile", read_only=True)
    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = ResourceComment
        fields = ["id", "user_id", "resource_id", "content", "created_at", "profiles"]
        read_only_fields = ["id", "user_id", "resource_id", "created_at", "profiles"]

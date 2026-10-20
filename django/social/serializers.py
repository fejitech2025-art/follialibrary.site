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
    like_count = serializers.IntegerField(source="likes.count", read_only=True)
    comment_count = serializers.IntegerField(source="comments.count", read_only=True)
    liked = serializers.SerializerMethodField()
    saved = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ["id", "author_id", "author", "body", "media", "media_url", "media_type", "created_at", "updated_at", "like_count", "comment_count", "liked", "saved", "is_owner"]
        read_only_fields = ["id", "author_id", "author", "media_url", "created_at", "updated_at", "like_count", "comment_count", "liked", "saved", "is_owner"]

    def get_media_url(self, obj):
        return storage_file_url(obj.media, self.context.get("request"))

    def get_liked(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.likes.filter(user=request.user).exists())

    def get_saved(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.bookmarks.filter(user=request.user).exists())

    def get_is_owner(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.author_id == request.user.pk)


class PostCommentSerializer(serializers.ModelSerializer):
    profiles = ProfileSerializer(source="user.profile", read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    parent_id = serializers.IntegerField(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = ["id", "post_id", "user_id", "parent_id", "content", "created_at", "profiles", "replies"]
        read_only_fields = ["id", "post_id", "user_id", "parent_id", "created_at", "profiles", "replies"]

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

    class Meta:
        model = PostComment
        fields = ["id", "post_id", "user_id", "parent_id", "content", "created_at", "profiles"]

from rest_framework import serializers

from accounts.serializers import ProfileSerializer
from config.serializer_fields import SafeStorageFileField
from config.storage_backends import storage_file_url
from library.serializers import ResourceSerializer
from library.models import Resource
from .models import BookClub, BookClubMembership, BookClubMessage, BookClubResource


class MembershipSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    profiles = ProfileSerializer(source="user.profile", read_only=True)

    class Meta:
        model = BookClubMembership
        fields = ["id", "user_id", "role", "joined_at", "profiles"]


class BookClubSerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField(read_only=True)
    profiles = ProfileSerializer(source="owner.profile", read_only=True)
    avatar = SafeStorageFileField(required=False, allow_null=True)
    avatar_url = serializers.SerializerMethodField()
    members = MembershipSerializer(source="memberships", many=True, read_only=True)
    book_club_members = MembershipSerializer(source="memberships", many=True, read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    is_member = serializers.SerializerMethodField()

    class Meta:
        model = BookClub
        fields = ["id", "owner_id", "name", "description", "avatar", "avatar_url", "created_at", "members", "book_club_members", "member_count", "profiles", "is_member"]
        read_only_fields = ["id", "owner_id", "created_at", "members", "book_club_members", "member_count", "profiles", "avatar_url", "is_member"]

    def get_avatar_url(self, obj):
        return storage_file_url(obj.avatar, self.context.get("request"))

    def get_is_member(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.memberships.filter(user=request.user).exists())


class BookClubResourceSerializer(serializers.ModelSerializer):
    club_id = serializers.IntegerField(read_only=True)
    resource_id = serializers.IntegerField(read_only=True)
    resources = ResourceSerializer(source="resource", read_only=True)
    added_by = serializers.IntegerField(source="added_by_id", read_only=True)

    class Meta:
        model = BookClubResource
        fields = ["id", "club_id", "resource_id", "added_by", "added_at", "resources"]


class BookClubResourceCreateSerializer(serializers.Serializer):
    resource_id = serializers.PrimaryKeyRelatedField(
        queryset=Resource.objects.filter(status="published"),
        source="resource",
    )

    def to_internal_value(self, data):
        if "resource_id" not in data and "resourceId" in data:
            data = data.copy()
            data["resource_id"] = data.get("resourceId")
        return super().to_internal_value(data)


class BookClubMessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(read_only=True)
    profiles = ProfileSerializer(source="sender.profile", read_only=True)
    reply_to_id = serializers.IntegerField(read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = BookClubMessage
        fields = ["id", "club_id", "sender_id", "content", "reply_to", "reply_to_id", "is_pinned", "created_at", "profiles", "is_owner"]
        read_only_fields = ["id", "club_id", "sender_id", "reply_to_id", "is_pinned", "created_at", "profiles", "is_owner"]

    def get_is_owner(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and request.user.pk == obj.sender_id)

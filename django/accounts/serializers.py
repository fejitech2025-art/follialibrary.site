from rest_framework import serializers

from config.serializer_fields import SafeStorageFileField
from config.storage_backends import storage_file_url
from .models import Follow, Notification, Profile
from ranking.service import rank_map


class ProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    id = serializers.IntegerField(source="user_id", read_only=True)
    avatar = SafeStorageFileField(required=False, allow_null=True)
    avatar_url = serializers.SerializerMethodField()
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    rank_position = serializers.SerializerMethodField()
    rank_score = serializers.SerializerMethodField()
    resource_count = serializers.SerializerMethodField()
    post_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ["id", "user_id", "username", "display_name", "avatar_url", "avatar", "bio", "location", "website", "follower_count", "following_count", "rank_position", "rank_score", "resource_count", "post_count", "is_following"]
        read_only_fields = ["id", "follower_count", "following_count", "rank_position", "rank_score", "resource_count", "post_count", "is_following"]

    def get_avatar_url(self, obj):
        return storage_file_url(obj.avatar, self.context.get("request"))

    def get_follower_count(self, obj):
        return obj.user.follower_edges.count()

    def get_following_count(self, obj):
        return obj.user.following_edges.count()

    def _rank(self, obj):
        cached = self.context.get("_rank_map")
        if cached is None:
            cached = rank_map("overall")
            self.context["_rank_map"] = cached
        return cached.get(obj.user_id, {"rank": None, "score": 0})

    def get_rank_position(self, obj):
        return self._rank(obj)["rank"]

    def get_rank_score(self, obj):
        return self._rank(obj)["score"]

    def get_resource_count(self, obj):
        return obj.user.resources.filter(status="published").count()

    def get_post_count(self, obj):
        return obj.user.posts.count()

    def get_is_following(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        return bool(user and user.is_authenticated and Follow.objects.filter(follower=user, following=obj.user).exists())


class NotificationSerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()
    actor_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "actor", "actor_id", "type", "post_id", "resource_id", "comment_id", "read", "created_at"]

    def get_actor(self, obj):
        return ProfileSerializer(obj.actor.profile, context=self.context).data

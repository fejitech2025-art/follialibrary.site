from rest_framework import serializers

from .models import Follow, Notification, Profile


class ProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user_id", read_only=True)
    avatar_url = serializers.CharField(read_only=True)
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    resource_count = serializers.SerializerMethodField()
    post_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ["id", "username", "display_name", "avatar_url", "avatar", "bio", "location", "website", "follower_count", "following_count", "resource_count", "post_count", "is_following"]
        read_only_fields = ["id", "follower_count", "following_count", "resource_count", "post_count", "is_following"]

    def get_follower_count(self, obj):
        return obj.user.follower_edges.count()

    def get_following_count(self, obj):
        return obj.user.following_edges.count()

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
        fields = ["id", "actor", "actor_id", "type", "post_id", "resource_id", "book_club_id", "read", "created_at"]

    def get_actor(self, obj):
        return ProfileSerializer(obj.actor.profile, context=self.context).data

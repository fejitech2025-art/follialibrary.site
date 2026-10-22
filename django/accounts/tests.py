from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase
from django.urls import resolve
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Follow, Notification, Profile, PushSubscription


User = get_user_model()




class NotificationAndPushApiTests(TestCase):
    def setUp(self):
        self.reader = User.objects.create_user(username="reader")
        self.other = User.objects.create_user(username="other")
        Profile.objects.update_or_create(user=self.reader, defaults={"username": "reader"})
        Profile.objects.update_or_create(user=self.other, defaults={"username": "other"})
        self.client = APIClient()

    def test_unread_count_and_read_actions_are_scoped_to_current_user(self):
        own = Notification.objects.create(recipient=self.reader, actor=self.other, type="follow")
        theirs = Notification.objects.create(recipient=self.other, actor=self.reader, type="follow")
        self.client.force_authenticate(self.reader)

        response = self.client.get("/api/notifications/unread-count/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(self.client.post(f"/api/notifications/{theirs.pk}/read/").status_code, 404)
        self.assertEqual(self.client.post(f"/api/notifications/{own.pk}/read/").status_code, 200)
        self.assertEqual(self.client.get("/api/notifications/unread-count/").data["count"], 0)

    def test_push_subscription_cannot_be_claimed_or_removed_by_another_user(self):
        endpoint = "https://fcm.googleapis.com/fcm/send/test-token"
        payload = {"endpoint": endpoint, "keys": {"p256dh": "public-key", "auth": "auth-key"}}
        self.client.force_authenticate(self.reader)
        invalid = self.client.post(
            "/api/push/subscriptions/",
            {"endpoint": "https://[invalid", "keys": {"p256dh": "public-key", "auth": "auth-key"}},
            format="json",
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(self.client.post("/api/push/subscriptions/", payload, format="json").status_code, 201)
        self.assertEqual(PushSubscription.objects.get(endpoint=endpoint).user, self.reader)

        self.client.force_authenticate(self.other)
        response = self.client.post("/api/push/subscriptions/", payload, format="json")
        self.assertEqual(response.status_code, 409)
        self.client.delete("/api/push/subscriptions/", {"endpoint": endpoint}, format="json")
        self.assertTrue(PushSubscription.objects.filter(endpoint=endpoint, user=self.reader).exists())
        self.assertFalse(PushSubscription.objects.filter(user=self.other).exists())

    def test_logout_clears_the_django_session(self):
        self.client.force_login(self.reader)
        response = self.client.post("/api/auth/logout/")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.client.get("/api/auth/me/").data["user"])

    def test_profile_likes_count_includes_posts_and_resources(self):
        from library.models import Resource, ResourceLike
        from social.models import Post, PostLike

        resource = Resource.objects.create(author=self.reader, title="A resource")
        post = Post.objects.create(author=self.reader, body="A post")
        ResourceLike.objects.create(user=self.other, resource=resource)
        PostLike.objects.create(user=self.other, post=post)

        response = self.client.get(f"/api/users/{self.reader.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["like_count"], 2)


class FollowNotificationTests(TestCase):
    def test_follow_creates_only_one_notification_for_a_new_relationship(self):
        reader = User.objects.create_user(username="reader")
        followed = User.objects.create_user(username="followed")
        Profile.objects.update_or_create(user=reader, defaults={"username": "reader"})
        Profile.objects.update_or_create(user=followed, defaults={"username": "followed"})
        client = APIClient()
        client.force_authenticate(reader)

        self.assertEqual(client.post(f"/api/users/{followed.pk}/follow/").status_code, 200)
        self.assertEqual(client.post(f"/api/users/{followed.pk}/follow/").status_code, 200)
        self.assertEqual(Notification.objects.filter(recipient=followed, type="follow").count(), 1)
        self.assertEqual(Follow.objects.filter(follower=reader, following=followed).count(), 1)


class DynamicProfileSuggestionTests(TestCase):
    def test_suggestions_exclude_self_and_followed_users_and_pick_up_new_profiles(self):
        reader = User.objects.create_user(username="suggest-reader")
        followed = User.objects.create_user(username="suggest-followed")
        candidate = User.objects.create_user(username="suggest-candidate")
        for user in (reader, followed, candidate):
            Profile.objects.update_or_create(user=user, defaults={"username": user.username})
        Follow.objects.create(follower=reader, following=followed)
        client = APIClient()
        client.force_authenticate(reader)

        first = client.get("/api/users/?suggested=1")
        ids = {item["user_id"] for item in first.data}
        self.assertIn(candidate.pk, ids)
        self.assertNotIn(reader.pk, ids)
        self.assertNotIn(followed.pk, ids)

        new_user = User.objects.create_user(username="suggest-new")
        Profile.objects.update_or_create(user=new_user, defaults={"username": new_user.username})
        refreshed = client.get("/api/users/?suggested=1")
        self.assertIn(new_user.pk, {item["user_id"] for item in refreshed.data})
        self.assertLessEqual(len(refreshed.data), 12)


class GoogleOnlyAuthenticationConfigurationTests(TestCase):
    def test_google_login_is_the_only_social_flow_and_callback_is_registered(self):
        google = settings.SOCIALACCOUNT_PROVIDERS["google"]
        self.assertTrue(settings.SOCIALACCOUNT_ONLY)
        self.assertTrue(settings.SOCIALACCOUNT_AUTO_SIGNUP)
        self.assertFalse(settings.SOCIALACCOUNT_LOGIN_ON_GET)
        self.assertTrue(google["EMAIL_AUTHENTICATION"])
        self.assertTrue(google["EMAIL_AUTHENTICATION_AUTO_CONNECT"])
        self.assertEqual(google["AUTH_PARAMS"]["prompt"], "select_account")
        self.assertEqual(resolve("/accounts/google/login/callback/").url_name, "google_callback")


class PublicUserCountPageTests(TestCase):
    def test_users_page_is_public_and_shows_registered_user_count(self):
        User.objects.create_user(username="public-reader")
        response = self.client.get(reverse("public-user-count"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Follia Library users")
        self.assertContains(response, ">1</output>")



from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Profile
from .models import Resource, ResourceComment


User = get_user_model()


class ResourceCommentReplyApiTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username="author")
        self.reader = User.objects.create_user(username="reader")
        self.other = User.objects.create_user(username="other")
        for user in (self.author, self.reader, self.other):
            Profile.objects.update_or_create(user=user, defaults={"username": user.username})
        self.resource = Resource.objects.create(author=self.author, title="Resource one")
        self.other_resource = Resource.objects.create(author=self.author, title="Resource two")
        self.client = APIClient()

    def test_authenticated_user_can_reply_and_thread_is_returned_nested(self):
        root = ResourceComment.objects.create(user=self.author, resource=self.resource, content="Root comment")
        self.client.force_authenticate(self.reader)

        response = self.client.post(
            f"/api/resources/{self.resource.pk}/comments/",
            {"content": "  A reply  ", "parent_id": root.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["content"], "A reply")
        self.assertEqual(response.data["parent_id"], root.pk)

        thread = self.client.get(f"/api/resources/{self.resource.pk}/comments/")
        self.assertEqual(len(thread.data), 1)
        self.assertEqual(len(thread.data[0]["replies"]), 1)
        self.assertEqual(thread.data[0]["replies"][0]["user_id"], self.reader.pk)

    def test_reply_must_target_a_root_comment_on_the_same_resource(self):
        unrelated = ResourceComment.objects.create(
            user=self.author,
            resource=self.other_resource,
            content="Unrelated comment",
        )
        root = ResourceComment.objects.create(user=self.author, resource=self.resource, content="Root")
        nested_reply = ResourceComment.objects.create(
            user=self.reader,
            resource=self.resource,
            parent=root,
            content="Already a reply",
        )
        self.client.force_authenticate(self.reader)

        for parent_id in (unrelated.pk, nested_reply.pk, "not-an-id"):
            response = self.client.post(
                f"/api/resources/{self.resource.pk}/comments/",
                {"content": "Reply", "parent_id": parent_id},
                format="json",
            )
            self.assertEqual(response.status_code, 400)

    def test_empty_comment_is_rejected_and_anonymous_user_cannot_post(self):
        self.client.force_authenticate(self.reader)
        response = self.client.post(
            f"/api/resources/{self.resource.pk}/comments/",
            {"content": "   "},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

        self.client.force_authenticate(user=None)
        response = self.client.post(
            f"/api/resources/{self.resource.pk}/comments/",
            {"content": "Anonymous"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

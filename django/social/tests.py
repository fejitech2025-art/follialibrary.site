from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Profile
from .models import Post, PostComment


User = get_user_model()


class PostCommentReplyApiTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username="author")
        self.reader = User.objects.create_user(username="reader")
        self.other = User.objects.create_user(username="other")
        for user in (self.author, self.reader, self.other):
            Profile.objects.update_or_create(user=user, defaults={"username": user.username})
        self.post = Post.objects.create(author=self.author, body="Image and video posts share this model")
        self.other_post = Post.objects.create(author=self.author, body="Another post")
        self.client = APIClient()

    def test_reply_is_saved_and_returned_with_its_parent(self):
        root = PostComment.objects.create(user=self.author, post=self.post, content="Root")
        self.client.force_authenticate(self.reader)

        response = self.client.post(
            f"/api/posts/{self.post.pk}/comments/",
            {"content": "Reply", "parent_id": root.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["parent_id"], root.pk)
        thread = self.client.get(f"/api/posts/{self.post.pk}/comments/")
        self.assertEqual(thread.data[0]["replies"][0]["content"], "Reply")

    def test_reply_cannot_target_another_post(self):
        unrelated = PostComment.objects.create(user=self.author, post=self.other_post, content="Other thread")
        self.client.force_authenticate(self.reader)
        response = self.client.post(
            f"/api/posts/{self.post.pk}/comments/",
            {"content": "Reply", "parent_id": unrelated.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_author_posts_endpoint_returns_images_and_videos_together(self):
        Post.objects.create(author=self.author, body="Image post", media_type="image")
        Post.objects.create(author=self.author, body="Video post", media_type="video")

        response = self.client.get(f"/api/posts/?author={self.author.pk}")
        self.assertEqual(response.status_code, 200)
        media_types = {item["media_type"] for item in response.data if item["media_type"]}
        self.assertEqual(media_types, {"image", "video"})

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.test import APIClient
import tempfile
from io import BytesIO
from types import SimpleNamespace
from PIL import Image

from accounts.models import Notification, Profile
from .models import ContentReport, Post, PostComment, PostCommentLike, PostMedia
from .views import MAX_POST_VIDEO_SIZE, validate_post_uploads


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
        self.assertEqual(thread.data[0]["profiles"]["user_id"], self.author.pk)
        self.assertEqual(thread.data[0]["profiles"]["id"], self.author.pk)
        self.assertEqual(thread.data[0]["replies"][0]["profiles"]["user_id"], self.reader.pk)

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


class PostMediaAndEngagementApiTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_root.cleanup)
        self.media_settings = override_settings(
            MEDIA_ROOT=self.media_root.name,
            STORAGES={
                "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
                "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
            },
        )
        self.media_settings.enable()
        self.addCleanup(self.media_settings.disable)

        self.author = User.objects.create_user(username="upload-author")
        self.reader = User.objects.create_user(username="upload-reader")
        Profile.objects.update_or_create(user=self.author, defaults={"username": self.author.username})
        Profile.objects.update_or_create(user=self.reader, defaults={"username": self.reader.username})
        self.post = Post.objects.create(author=self.author, body="A post with comments")
        self.client = APIClient()
        self.client.force_authenticate(self.reader)

    def test_video_limit_accepts_40_mib_and_rejects_one_byte_over(self):
        accepted = SimpleNamespace(content_type="video/mp4", size=MAX_POST_VIDEO_SIZE,
                                   read=lambda count: b"\x00\x00\x00\x18ftypmp42",
                                   seek=lambda position: None)
        self.assertEqual(validate_post_uploads([accepted]), "")

        accepted_upload = SimpleUploadedFile("clip.mp4", b"\x00\x00\x00\x18ftypmp42", content_type="video/mp4")
        response = self.client.post("/api/posts/", {"body": "Trimmed clip", "media": accepted_upload}, format="multipart")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["media_type"], "video")

        oversized = SimpleNamespace(content_type="video/mp4", size=MAX_POST_VIDEO_SIZE + 1,
                                     read=lambda count: b"\x00\x00\x00\x18ftypmp42",
                                     seek=lambda position: None)
        self.assertEqual(validate_post_uploads([oversized]), "Videos must be 40 MB or smaller.")

    def test_multiple_images_are_saved_as_separate_post_media(self):
        def png_bytes(color):
            buffer = BytesIO()
            Image.new("RGB", (2, 2), color).save(buffer, format="PNG")
            return buffer.getvalue()

        first = SimpleUploadedFile("first.png", png_bytes("red"), content_type="image/png")
        second = SimpleUploadedFile("second.png", png_bytes("blue"), content_type="image/png")
        response = self.client.post("/api/posts/", {"body": "Two images #weekend", "media": [first, second]}, format="multipart")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data["media_items"]), 2)
        self.assertEqual(PostMedia.objects.filter(post_id=response.data["id"]).count(), 2)

    def test_like_and_comment_contracts_accept_expected_requests_and_persist(self):
        like_url = f"/api/posts/{self.post.pk}/like/"
        first = self.client.post(like_url)
        duplicate = self.client.post(like_url)
        self.assertEqual(first.status_code, 200, first.data)
        self.assertEqual(duplicate.data, {"liked": True, "count": 1})
        removed = self.client.delete(like_url)
        self.assertEqual(removed.data, {"liked": False, "count": 0})

        comment_url = f"/api/posts/{self.post.pk}/comments/"
        created = self.client.post(comment_url, {"content": "A useful comment from the community."}, format="json")
        self.assertEqual(created.status_code, 201, created.data)
        listed = self.client.get(comment_url)
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data[0]["content"], "A useful comment from the community.")

        invalid = self.client.post(comment_url, {"content": "   "}, format="json")
        self.assertEqual(invalid.status_code, 400)

    def test_like_and_comment_requests_work_with_session_auth_and_csrf_enforced(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.reader)
        csrf_response = client.get("/api/auth/csrf/")
        csrf_token = csrf_response.data["csrfToken"]

        liked = client.post(f"/api/posts/{self.post.pk}/like/", HTTP_X_CSRFTOKEN=csrf_token)
        commented = client.post(
            f"/api/posts/{self.post.pk}/comments/",
            {"content": "A session authenticated comment."},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(liked.status_code, 200, liked.data)
        self.assertEqual(commented.status_code, 201, commented.data)

    def test_post_hashtag_limit_is_enforced_on_create_and_edit(self):
        tags = "#one #two #three #four #five #six"
        created = self.client.post("/api/posts/", {"body": tags}, format="json")
        self.assertEqual(created.status_code, 400)
        self.assertIn("five", created.data["detail"])
        self.client.force_authenticate(self.author)
        edit = self.client.patch(f"/api/posts/{self.post.pk}/", {"body": tags}, format="json")
        self.assertEqual(edit.status_code, 400)

    def test_comment_likes_are_unique_and_notify_only_the_comment_author(self):
        comment = PostComment.objects.create(user=self.author, post=self.post, content="Read this")
        url = f"/api/posts/{self.post.pk}/comments/{comment.pk}/like/"
        first = self.client.post(url)
        retry = self.client.post(url)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first["Content-Type"], "application/json")
        self.assertEqual(first.data, {"liked": True, "count": 1})
        self.assertEqual(retry.data, {"liked": True, "count": 1})
        self.assertEqual(PostCommentLike.objects.filter(comment=comment).count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.author, type="comment_like").count(), 1)

        self.client.delete(url)
        self.client.post(url)
        self.assertEqual(Notification.objects.filter(recipient=self.author, type="comment_like").count(), 1)

        own_comment = PostComment.objects.create(user=self.reader, post=self.post, content="My own")
        self.client.post(f"/api/posts/{self.post.pk}/comments/{own_comment.pk}/like/")
        self.assertEqual(Notification.objects.filter(recipient=self.reader, type="comment_like").count(), 0)

        self.client.force_authenticate(user=None)
        unauthorized = self.client.post(url)
        self.assertEqual(unauthorized.status_code, 403)
        self.assertEqual(unauthorized["Content-Type"], "application/json")

    def test_duplicate_reports_do_not_create_extra_rows_and_report_reason_is_validated(self):
        report_url = f"/api/posts/{self.post.pk}/report/"
        first = self.client.post(report_url, {"reason": "spam", "description": "Repeated links"}, format="json")
        retry = self.client.post(report_url, {"reason": "spam"}, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(retry.status_code, 200)
        self.assertTrue(retry.data["duplicate"])
        self.assertEqual(ContentReport.objects.filter(reporter=self.reader, post=self.post).count(), 1)

        invalid = self.client.post(report_url, {"reason": "made-up"}, format="json")
        self.assertEqual(invalid.status_code, 400)

        admin_client = APIClient()
        admin_client.force_login(self.reader)
        self.assertEqual(admin_client.get("/admin/social/contentreport/").status_code, 302)
        admin_user = User.objects.create_superuser(username="report-admin", email="admin@example.test", password="safe-test-password")
        admin_client.force_login(admin_user)
        self.assertEqual(admin_client.get("/admin/social/contentreport/").status_code, 200)

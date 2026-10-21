from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.test import APIClient
from accounts.models import Notification
import tempfile

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

    def test_comment_like_is_separate_unique_and_notifies_the_author(self):
        comment = ResourceComment.objects.create(user=self.author, resource=self.resource, content="Helpful note")
        self.client.force_authenticate(self.reader)
        url = f"/api/resources/{self.resource.pk}/comments/{comment.pk}/like/"
        first = self.client.post(url)
        retry = self.client.post(url)
        self.assertEqual(first.data, {"liked": True, "count": 1})
        self.assertEqual(retry.data, {"liked": True, "count": 1})
        self.assertEqual(comment.likes.count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.author, type="comment_like").count(), 1)

        self.client.delete(url)
        self.client.post(url)
        self.assertEqual(Notification.objects.filter(recipient=self.author, type="comment_like").count(), 1)


class ResourcePreviewAndWatermarkTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_root.cleanup)
        self.media_settings = override_settings(MEDIA_ROOT=self.media_root.name, FOLLIA_PUBLIC_URL="https://library.example")
        self.media_settings.enable()
        self.addCleanup(self.media_settings.disable)
        self.author = User.objects.create_user(username="file-owner")
        Profile.objects.update_or_create(user=self.author, defaults={"username": self.author.username})
        self.client = APIClient()

    def test_production_watermark_rejects_a_localhost_site_url(self):
        from config.watermark import WatermarkProcessingError, watermarked_download

        with override_settings(DEBUG=False, FOLLIA_PUBLIC_URL="http://localhost:5173", FRONTEND_URL="http://localhost:5173"):
            with self.assertRaisesRegex(WatermarkProcessingError, "public Follia Library site"):
                watermarked_download(None, "cover.png", "file-owner")

    def test_pdf_preview_serves_original_inline_and_download_contains_watermark(self):
        try:
            import pymupdf as fitz
        except ImportError:
            self.skipTest("PyMuPDF is not installed")

        original = fitz.open()
        page = original.new_page()
        page.insert_text((40, 50), "Original PDF page")
        original_bytes = original.tobytes()
        original.close()
        resource = Resource.objects.create(
            author=self.author,
            title="Guide",
            file=SimpleUploadedFile("guide.pdf", original_bytes, content_type="application/pdf"),
            file_name="guide.pdf",
            file_type="application/pdf",
            is_free=True,
        )

        preview = self.client.get(f"/api/resources/{resource.pk}/preview/")
        self.assertEqual(preview.status_code, 200)
        self.assertIn("inline", preview["Content-Disposition"])
        self.assertNotIn("X-Frame-Options", preview)
        preview_bytes = b"".join(preview.streaming_content)
        preview.close()
        preview_doc = fitz.open(stream=preview_bytes, filetype="pdf")
        self.assertEqual(preview_doc[0].get_images(full=True), [])
        preview_doc.close()

        download = self.client.get(f"/api/resources/{resource.pk}/file/")
        self.assertEqual(download.status_code, 200)
        self.assertIn("attachment", download["Content-Disposition"])
        downloaded_bytes = b"".join(download.streaming_content)
        download.close()
        downloaded_doc = fitz.open(stream=downloaded_bytes, filetype="pdf")
        self.assertTrue(downloaded_doc[0].get_images(full=True))
        downloaded_doc.close()

        with resource.file.open("rb") as stored:
            untouched = fitz.open(stream=stored.read(), filetype="pdf")
        self.assertEqual(untouched[0].get_images(full=True), [])
        untouched.close()

    def test_image_download_contains_a_visible_watermark(self):
        try:
            from PIL import Image, ImageChops
        except ImportError:
            self.skipTest("Pillow is not installed")
        from io import BytesIO

        source = Image.new("RGB", (900, 600), (70, 120, 160))
        source_buffer = BytesIO()
        source.save(source_buffer, format="PNG")
        resource = Resource.objects.create(
            author=self.author,
            title="Image resource",
            file=SimpleUploadedFile("cover.png", source_buffer.getvalue(), content_type="image/png"),
            file_name="cover.png",
            file_type="application/octet-stream",
            is_free=True,
        )

        response = self.client.get(f"/api/resources/{resource.pk}/file/")
        self.assertEqual(response.status_code, 200)
        output = Image.open(BytesIO(b"".join(response.streaming_content))).convert("RGB")
        response.close()
        original_image = Image.new("RGB", (900, 600), (70, 120, 160))
        self.assertIsNotNone(ImageChops.difference(original_image, output).getbbox())

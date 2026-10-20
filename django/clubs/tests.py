from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Profile
from accounts.models import Notification
from library.models import Resource
from .models import BookClub, BookClubMembership, BookClubResource


User = get_user_model()


class BookClubResourceApiTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner")
        self.admin = User.objects.create_user(username="admin")
        self.member = User.objects.create_user(username="member")
        for user in (self.owner, self.admin, self.member):
            Profile.objects.update_or_create(user=user, defaults={"username": user.username})
        self.club = BookClub.objects.create(owner=self.owner, name="Reading room")
        BookClubMembership.objects.create(club=self.club, user=self.owner, role="owner")
        BookClubMembership.objects.create(club=self.club, user=self.admin, role="admin")
        BookClubMembership.objects.create(club=self.club, user=self.member, role="member")
        self.resource = Resource.objects.create(author=self.owner, title="Published book")
        self.client = APIClient()

    def test_admin_can_add_published_book_without_duplicate_links(self):
        self.client.force_authenticate(self.admin)
        url = f"/api/clubs/{self.club.pk}/resources/"

        response = self.client.post(url, {"resource_id": self.resource.pk}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["created"])
        self.assertEqual(BookClubResource.objects.filter(club=self.club, resource=self.resource).count(), 1)

        duplicate = self.client.post(url, {"resourceId": self.resource.pk}, format="json")
        self.assertEqual(duplicate.status_code, 200)
        self.assertFalse(duplicate.data["created"])
        self.assertEqual(BookClubResource.objects.filter(club=self.club, resource=self.resource).count(), 1)

    def test_non_admin_and_invalid_requests_are_rejected(self):
        url = f"/api/clubs/{self.club.pk}/resources/"
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.post(url, {"resource_id": self.resource.pk}, format="json").status_code, 403)

        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.post(url, {}, format="json").status_code, 400)
        self.assertEqual(
            self.client.post(url, {"resource_id": 999999}, format="json").status_code,
            400,
        )

    def test_repeating_a_role_action_does_not_duplicate_notifications(self):
        self.client.force_authenticate(self.owner)
        url = f"/api/clubs/{self.club.pk}/members/{self.member.pk}/"

        self.assertEqual(self.client.post(url, {"action": "promote"}, format="json").status_code, 200)
        self.assertEqual(self.client.post(url, {"action": "promote"}, format="json").status_code, 200)
        self.assertEqual(Notification.objects.filter(recipient=self.member, type="book_club_admin").count(), 1)

        self.assertEqual(self.client.post(url, {"action": "demote"}, format="json").status_code, 200)
        self.assertEqual(Notification.objects.filter(recipient=self.member, type="book_club_admin").count(), 2)

    def test_club_message_is_returned_after_being_saved(self):
        self.client.force_authenticate(self.admin)
        url = f"/api/clubs/{self.club.pk}/messages/"

        sent = self.client.post(url, {"content": "A new chat message"}, format="json")
        self.assertEqual(sent.status_code, 201)
        self.assertTrue(sent.data["id"])
        self.assertEqual(sent.data["content"], "A new chat message")

        history = self.client.get(url)
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.data[0]["id"], sent.data["id"])

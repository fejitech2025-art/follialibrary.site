import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Profile
from messaging.models import Conversation, DirectMessage

User = get_user_model()


class PrivateMessagingApiTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username="message-alice")
        self.bob = User.objects.create_user(username="message-bob")
        self.outsider = User.objects.create_user(username="message-outsider")
        for user in (self.alice, self.bob, self.outsider):
            Profile.objects.update_or_create(user=user, defaults={"username": user.username})
        self.alice_client = APIClient()
        self.alice_client.force_authenticate(self.alice)
        self.bob_client = APIClient()
        self.bob_client.force_authenticate(self.bob)
        self.outsider_client = APIClient()
        self.outsider_client.force_authenticate(self.outsider)

    def test_conversation_is_reused_and_listed_after_first_persisted_message(self):
        first = self.alice_client.post("/api/messages/conversations/", {"user_id": self.bob.pk}, format="json")
        second = self.bob_client.post("/api/messages/conversations/", {"user_id": self.alice.pk}, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.data["id"], second.data["id"])
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(self.bob_client.get("/api/messages/conversations/").data, [])

        client_id = str(uuid.uuid4())
        url = f"/api/messages/conversations/{first.data['id']}/messages/"
        sent = self.alice_client.post(url, {"client_id": client_id, "message_type": "text", "body": "Hello privately"}, format="json")
        retry = self.alice_client.post(url, {"client_id": client_id, "message_type": "text", "body": "Hello privately"}, format="json")
        self.assertEqual(sent.status_code, 201, sent.data)
        self.assertEqual(retry.status_code, 200, retry.data)
        self.assertEqual(DirectMessage.objects.count(), 1)
        self.assertEqual(len(self.bob_client.get("/api/messages/conversations/").data), 1)

    def test_only_conversation_participants_can_read_or_send(self):
        conversation = self.alice_client.post("/api/messages/conversations/", {"user_id": self.bob.pk}, format="json").data
        url = f"/api/messages/conversations/{conversation['id']}/messages/"
        self.assertEqual(self.outsider_client.get(url).status_code, 404)
        response = self.outsider_client.post(url, {"client_id": str(uuid.uuid4()), "body": "Intrusion"}, format="json")
        self.assertEqual(response.status_code, 404)

    def test_a_block_prevents_new_conversations_and_message_sends(self):
        conversation = self.alice_client.post("/api/messages/conversations/", {"user_id": self.bob.pk}, format="json").data
        self.bob_client.post("/api/messages/blocks/", {"user_id": self.alice.pk}, format="json")
        blocked_start = self.alice_client.post("/api/messages/conversations/", {"user_id": self.bob.pk}, format="json")
        self.assertEqual(blocked_start.status_code, 403)
        url = f"/api/messages/conversations/{conversation['id']}/messages/"
        blocked_send = self.alice_client.post(url, {"client_id": str(uuid.uuid4()), "body": "Cannot send"}, format="json")
        self.assertEqual(blocked_send.status_code, 403)

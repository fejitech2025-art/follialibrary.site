import uuid
import mimetypes

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Count, Max, OuterRef, Q, Subquery
from django.http import FileResponse
from django.utils import timezone
from rest_framework.decorators import api_view, parser_classes, permission_classes, throttle_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle

from accounts.models import notify
from config.storage_backends import media_storage_available_for_upload
from social.models import Post
from .models import Conversation, DirectMessage, MessageReport, UserBlock
from .realtime import send_user_event
from .serializers import DirectMessageSerializer

User = get_user_model()
MAX_VOICE_SIZE = 20 * 1024 * 1024


class _MessageUserThrottle(SimpleRateThrottle):
    def allow_request(self, request, view):
        if request.method != "POST":
            return True
        return super().allow_request(request, view)

    def get_cache_key(self, request, view):
        if not request.user.is_authenticated:
            return None
        return self.cache_format % {"scope": self.scope, "ident": request.user.pk}


class MessageSendThrottle(_MessageUserThrottle):
    scope = "message_send"


class MessageReportThrottle(_MessageUserThrottle):
    scope = "message_report"
STICKERS = {"📚", "✨", "💛", "🎉", "🤔", "☕", "🦊", "🐈", "🌱", "🌟", "👏", "❤️"}


def paired_users(user, other_id):
    return User.objects.filter(pk=other_id).first()


def blocked_between(first_id, second_id):
    return UserBlock.objects.filter(
        Q(blocker_id=first_id, blocked_id=second_id) |
        Q(blocker_id=second_id, blocked_id=first_id)
    ).exists()


def conversation_for(user, conversation_id):
    conversation = Conversation.objects.filter(pk=conversation_id).first()
    if not conversation or user.pk not in (conversation.user_one_id, conversation.user_two_id):
        return None, Response({"detail": "Conversation not found."}, status=404)
    if UserBlock.objects.filter(blocker_id__in=[conversation.user_one_id, conversation.user_two_id],
                                blocked_id__in=[conversation.user_one_id, conversation.user_two_id]).exists():
        other_id = conversation.user_two_id if user.pk == conversation.user_one_id else conversation.user_one_id
        if UserBlock.objects.filter(blocker_id=other_id, blocked_id=user.pk).exists():
            return None, Response({"detail": "You cannot access this conversation."}, status=403)
    return conversation, None


def other_user(conversation, user):
    return conversation.user_two if conversation.user_one_id == user.pk else conversation.user_one


def conversation_payload(conversation, user, last_message=None, unread_count=None, block_pairs=None):
    other = other_user(conversation, user)
    profile = getattr(other, "profile", None)
    if block_pairs is None:
        blocked_by_me = UserBlock.objects.filter(blocker=user, blocked=other).exists()
        blocked_you = UserBlock.objects.filter(blocker=other, blocked=user).exists()
    else:
        blocked_by_me = (user.pk, other.pk) in block_pairs
        blocked_you = (other.pk, user.pk) in block_pairs
    is_blocked = blocked_by_me or blocked_you
    message_data = DirectMessageSerializer(last_message).data if last_message else None
    return {
        "id": conversation.pk,
        "participant": {
            "id": other.pk,
            "user_id": other.pk,
            "username": profile.username if profile else other.username,
            "display_name": (profile.display_name or profile.username) if profile else other.get_full_name() or other.username,
            "avatar_url": profile.avatar_url if profile else "",
        },
        "last_message": message_data,
        "last_message_at": last_message.created_at.isoformat() if last_message else None,
        "unread_count": unread_count if unread_count is not None else conversation.messages.filter(sender=other, read_at__isnull=True).count(),
        "blocked": is_blocked,
        "blocked_by_me": blocked_by_me,
        "blocked_you": blocked_you,
    }


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def conversations(request):
    if request.method == "POST":
        try:
            target_id = int(request.data.get("user_id"))
        except (TypeError, ValueError):
            return Response({"detail": "Choose a valid user to message."}, status=400)
        target = paired_users(request.user, target_id)
        if not target:
            return Response({"detail": "User not found."}, status=404)
        if target.pk == request.user.pk:
            return Response({"detail": "You cannot start a conversation with yourself."}, status=400)
        if blocked_between(request.user.pk, target.pk):
            return Response({"detail": "This conversation is unavailable because one of you has blocked the other."}, status=403)
        first, second = sorted((request.user, target), key=lambda person: person.pk)
        try:
            with transaction.atomic():
                conversation, _ = Conversation.objects.get_or_create(user_one=first, user_two=second)
        except IntegrityError:
            conversation = Conversation.objects.get(user_one=first, user_two=second)
        return Response({"id": conversation.pk, "participant": {"id": target.pk, "username": getattr(getattr(target, "profile", None), "username", target.username),
                         "display_name": getattr(getattr(target, "profile", None), "display_name", "") or target.username,
                         "avatar_url": getattr(getattr(target, "profile", None), "avatar_url", "")},
                         "created": conversation.messages.count() == 0}, status=201)

    latest_message = DirectMessage.objects.filter(conversation_id=OuterRef("pk")).order_by("-created_at", "-id").values("pk")[:1]
    query = Conversation.objects.filter(Q(user_one=request.user) | Q(user_two=request.user))
    query = query.annotate(last_message_id=Subquery(latest_message), last_activity=Max("messages__created_at"),
                           unread_count=Count("messages", filter=Q(messages__read_at__isnull=True) & ~Q(messages__sender=request.user)))
    query = query.filter(last_message_id__isnull=False).order_by("-last_activity", "-id")
    conversations_list = list(query[:50].select_related("user_one__profile", "user_two__profile"))
    message_ids = [item.last_message_id for item in conversations_list]
    last_messages = {
        message.pk: message
        for message in DirectMessage.objects.filter(pk__in=message_ids)
        .select_related("sender__profile", "shared_post__author__profile")
        .prefetch_related("shared_post__media_items")
    }
    user_ids = {request.user.pk}
    for item in conversations_list:
        user_ids.update((item.user_one_id, item.user_two_id))
    block_pairs = set(UserBlock.objects.filter(blocker_id__in=user_ids, blocked_id__in=user_ids)
                      .values_list("blocker_id", "blocked_id"))
    payload = [conversation_payload(item, request.user, last_messages.get(item.last_message_id), item.unread_count, block_pairs)
               for item in conversations_list]
    return Response(payload)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def conversation_detail(request, conversation_id):
    conversation, error = conversation_for(request.user, conversation_id)
    if error:
        return error
    last_message = conversation.messages.order_by("-created_at", "-id").first()
    return Response(conversation_payload(conversation, request.user, last_message))


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser, MultiPartParser, FormParser])
@throttle_classes([MessageSendThrottle])
def conversation_messages(request, conversation_id):
    conversation, error = conversation_for(request.user, conversation_id)
    if error:
        return error
    recipient = other_user(conversation, request.user)
    if request.method == "GET":
        query = conversation.messages.select_related("sender", "shared_post__author__profile").prefetch_related("shared_post__media_items")
        before = request.query_params.get("before")
        if before:
            cursor = query.filter(pk=before).first()
            if not cursor:
                return Response({"detail": "Message cursor not found."}, status=400)
            query = query.filter(Q(created_at__lt=cursor.created_at) | Q(created_at=cursor.created_at, pk__lt=cursor.pk))
        rows = list(query.order_by("-created_at", "-id")[:51])
        has_more = len(rows) > 50
        rows = list(reversed(rows[:50]))
        return Response({"messages": DirectMessageSerializer(rows, many=True, context={"request": request}).data,
                         "has_more": has_more, "next_before": rows[0].pk if has_more and rows else None})

    if blocked_between(request.user.pk, recipient.pk):
        return Response({"detail": "Messages cannot be sent while this block is active."}, status=403)
    raw_client_id = request.data.get("client_id")
    try:
        client_id = uuid.UUID(str(raw_client_id))
    except (ValueError, TypeError, AttributeError):
        return Response({"detail": "A valid client_id is required to prevent duplicate messages."}, status=400)
    message_type = request.data.get("message_type", "text")
    body = str(request.data.get("body", "")).strip()
    upload = request.FILES.get("file")
    shared_post = None
    duration = None
    if message_type == "text":
        if not body or len(body) > 3000:
            return Response({"detail": "Text messages must contain 1 to 3,000 characters."}, status=400)
    elif message_type == "sticker":
        if body not in STICKERS:
            return Response({"detail": "Choose a sticker from the available sticker set."}, status=400)
    elif message_type == "post_share":
        try:
            shared_post_id = int(request.data.get("post_id"))
        except (TypeError, ValueError):
            return Response({"detail": "Choose a post to share."}, status=400)
        shared_post = Post.objects.filter(pk=shared_post_id).select_related("author__profile").first()
        if not shared_post:
            return Response({"detail": "This post is no longer available."}, status=404)
    elif message_type == "voice":
        if not upload or not media_storage_available_for_upload():
            return Response({"detail": "Voice note storage is unavailable."}, status=503 if not media_storage_available_for_upload() else 400)
        if upload.size > MAX_VOICE_SIZE:
            return Response({"detail": "Voice notes must be 20 MB or smaller."}, status=400)
        if not valid_audio_upload(upload):
            return Response({"detail": "Choose a supported audio recording."}, status=400)
        try:
            duration = int(request.data.get("duration_seconds", 0))
        except (TypeError, ValueError):
            duration = 0
        if duration < 1 or duration > 180:
            return Response({"detail": "Voice notes must be between 1 and 180 seconds."}, status=400)
    else:
        return Response({"detail": "Choose a supported message type."}, status=400)

    try:
        with transaction.atomic():
            message, created = DirectMessage.objects.get_or_create(
                conversation=conversation, sender=request.user, client_id=client_id,
                defaults={"message_type": message_type, "body": body, "attachment": upload or "",
                          "duration_seconds": duration, "shared_post": shared_post},
            )
            if created:
                conversation.save(update_fields=["updated_at"])
    except IntegrityError:
        message = DirectMessage.objects.get(conversation=conversation, sender=request.user, client_id=client_id)
        created = False
    data = DirectMessageSerializer(message, context={"request": request}).data
    if created:
        for user_id in (conversation.user_one_id, conversation.user_two_id):
            send_user_event(user_id, {"type": "message_new", "conversation_id": conversation.pk, "message": data})
        notify(recipient, request.user, "message", event_key=f"direct-message:{message.pk}")
    return Response(data, status=201 if created else 200)


def valid_audio_upload(upload):
    try:
        header = upload.read(16)
        upload.seek(0)
    except (OSError, AttributeError):
        return False
    return (
        header.startswith((b"OggS", b"ID3", b"\x1aE\xdf\xa3")) or
        header.startswith(b"RIFF") and header[8:12] == b"WAVE" or
        header[4:8] == b"ftyp" or
        header.startswith((b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"))
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_read(request, conversation_id):
    conversation, error = conversation_for(request.user, conversation_id)
    if error:
        return error
    now = timezone.now()
    updated = conversation.messages.filter(read_at__isnull=True).exclude(sender=request.user).update(read_at=now)
    recipient_id = other_user(conversation, request.user).pk
    send_user_event(recipient_id, {"type": "read_receipt", "conversation_id": conversation.pk, "reader_id": request.user.pk, "read_at": now.isoformat()})
    return Response({"read": True, "updated": updated})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def message_media(request, message_id):
    message = DirectMessage.objects.filter(pk=message_id).select_related("conversation").first()
    if not message or request.user.pk not in (message.conversation.user_one_id, message.conversation.user_two_id):
        return Response({"detail": "Media not found."}, status=404)
    if UserBlock.objects.filter(blocker_id__in=[message.conversation.user_one_id, message.conversation.user_two_id],
                                blocked_id__in=[message.conversation.user_one_id, message.conversation.user_two_id]).exists():
        other_id = message.conversation.user_two_id if request.user.pk == message.conversation.user_one_id else message.conversation.user_one_id
        if UserBlock.objects.filter(blocker_id=other_id, blocked_id=request.user.pk).exists():
            return Response({"detail": "Media not found."}, status=404)
    if not message.attachment:
        return Response({"detail": "Media not found."}, status=404)
    filename = message.attachment.name.rsplit("/", 1)[-1]
    content_type = mimetypes.guess_type(filename)[0] or "audio/webm"
    return FileResponse(message.attachment.open("rb"), as_attachment=False, filename=filename,
                        content_type=content_type)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def blocks(request):
    if request.method == "GET":
        rows = UserBlock.objects.filter(blocker=request.user).select_related("blocked__profile")
        return Response([{"user_id": row.blocked_id, "username": getattr(getattr(row.blocked, "profile", None), "username", row.blocked.username)} for row in rows])
    try:
        target_id = int(request.data.get("user_id"))
    except (TypeError, ValueError):
        return Response({"detail": "Choose a valid user to block."}, status=400)
    target = User.objects.filter(pk=target_id).first()
    if not target:
        return Response({"detail": "User not found."}, status=404)
    if target.pk == request.user.pk:
        return Response({"detail": "You cannot block yourself."}, status=400)
    UserBlock.objects.get_or_create(blocker=request.user, blocked=target)
    send_user_event(target.pk, {"type": "user_blocked", "user_id": request.user.pk})
    return Response({"blocked": True, "user_id": target.pk})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def unblock(request, user_id):
    UserBlock.objects.filter(blocker=request.user, blocked_id=user_id).delete()
    send_user_event(user_id, {"type": "user_unblocked", "user_id": request.user.pk})
    return Response({"blocked": False})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageReportThrottle])
def report_message(request, message_id):
    message = DirectMessage.objects.filter(pk=message_id).select_related("conversation").first()
    if not message or request.user.pk not in (message.conversation.user_one_id, message.conversation.user_two_id):
        return Response({"detail": "Message not found."}, status=404)
    reason = request.data.get("reason", "other")
    if reason not in dict(MessageReport.REASONS):
        return Response({"detail": "Choose a valid report reason."}, status=400)
    description = str(request.data.get("description", "")).strip()
    if len(description) > 500:
        return Response({"detail": "Report explanations can be up to 500 characters."}, status=400)
    _, created = MessageReport.objects.get_or_create(reporter=request.user, message=message,
                                                     defaults={"reason": reason, "description": description})
    return Response({"reported": True, "duplicate": not created}, status=201 if created else 200)


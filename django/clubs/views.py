import uuid

from django.db.models import Q
from django.db import transaction
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from accounts.models import notify
from config.storage_backends import media_storage_available_for_upload
from library.models import Resource
from library.serializers import ResourceSerializer
from .models import BookClub, BookClubMembership, BookClubMessage, BookClubResource
from .realtime import broadcast_club_event, message_payload
from .serializers import BookClubMessageSerializer, BookClubResourceCreateSerializer, BookClubResourceSerializer, BookClubSerializer, MembershipSerializer


def get_member(club_id, user):
    if not user.is_authenticated:
        return None
    return BookClubMembership.objects.filter(club_id=club_id, user=user).select_related("club").first()


def can_moderate(member):
    return bool(member and member.role in {"owner", "admin"})


def validate_club_avatar(request):
    avatar = request.FILES.get("avatar")
    if not avatar:
        return None
    if not (avatar.content_type or "").startswith("image/") or avatar.size > 5 * 1024 * 1024:
        return Response({"detail": "Book Club avatars must be images smaller than 5 MB."}, status=400)
    if not media_storage_available_for_upload():
        return Response({"detail": "Cloudflare R2 media storage is not configured."}, status=503)
    return None


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def clubs(request):
    if request.method == "GET":
        query = BookClub.objects.select_related("owner__profile").prefetch_related("memberships__user__profile")
        search = request.query_params.get("q", "").strip()
        if search:
            query = query.filter(Q(name__icontains=search) | Q(description__icontains=search))
        return Response(BookClubSerializer(query[:40], many=True, context={"request": request}).data)
    if not request.user.is_authenticated:
        return Response({"detail": "Sign in to create a Book Club."}, status=401)
    avatar_error = validate_club_avatar(request)
    if avatar_error:
        return avatar_error
    serializer = BookClubSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    club = serializer.save(owner=request.user)
    BookClubMembership.objects.create(club=club, user=request.user, role="owner")
    return Response(BookClubSerializer(club, context={"request": request}).data, status=201)


@api_view(["GET", "PATCH"])
@permission_classes([AllowAny])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def club_detail(request, club_id):
    club = BookClub.objects.select_related("owner__profile").prefetch_related("memberships__user__profile").filter(pk=club_id).first()
    if not club:
        return Response({"detail": "Book Club not found."}, status=404)
    if request.method == "GET":
        return Response(BookClubSerializer(club, context={"request": request}).data)
    if not request.user.is_authenticated or club.owner_id != request.user.pk:
        return Response({"detail": "Only the owner can update this Book Club."}, status=403)
    avatar_error = validate_club_avatar(request)
    if avatar_error:
        return avatar_error
    serializer = BookClubSerializer(club, data=request.data, partial=True, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def club_membership(request, club_id):
    member = get_member(club_id, request.user)
    return Response(MembershipSerializer(member).data if member else None)


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def join_club(request, club_id):
    club = BookClub.objects.filter(pk=club_id).first()
    if not club:
        return Response({"detail": "Book Club not found."}, status=404)
    if request.method == "POST":
        member, created = BookClubMembership.objects.get_or_create(club=club, user=request.user, defaults={"role": "member"})
        if created:
            notify(club.owner, request.user, "book_club_join", book_club_id=club.pk, event_key=f"book-club-join:{member.pk}")
        return Response(MembershipSerializer(member).data, status=201 if created else 200)
    member = get_member(club_id, request.user)
    if member and member.role != "owner":
        member.delete()
    return Response({"joined": False})


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def manage_member(request, club_id, member_id):
    club = BookClub.objects.filter(pk=club_id).first()
    if not club or club.owner_id != request.user.pk:
        return Response({"detail": "Only the owner can manage members."}, status=403)
    member = BookClubMembership.objects.select_for_update().filter(
        Q(pk=member_id) | Q(user_id=member_id),
        club=club,
    ).first()
    if not member:
        return Response({"detail": "Member not found."}, status=404)
    action = request.data.get("action", "remove")
    if member.role == "owner":
        return Response({"detail": "The owner role cannot be changed."}, status=400)
    if request.method == "DELETE" or action == "remove":
        user_id = member.user_id
        member.delete()
        return Response({"removed": True, "user_id": user_id})
    new_role = "admin" if action == "promote" else "member"
    if member.role == new_role:
        return Response(MembershipSerializer(member).data)
    member.role = new_role
    member.save(update_fields=["role"])
    notify(
        member.user,
        request.user,
        "book_club_admin",
        book_club_id=club.pk,
        event_key=f"book-club-role:{member.pk}:{uuid.uuid4().hex}",
    )
    return Response(MembershipSerializer(member).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def messages(request, club_id):
    if not get_member(club_id, request.user):
        return Response({"detail": "Join this Book Club to use its chat."}, status=403)
    if request.method == "GET":
        query = BookClubMessage.objects.filter(club_id=club_id).select_related("sender__profile", "reply_to")
        return Response(BookClubMessageSerializer(query[:250], many=True, context={"request": request}).data)
    content = request.data.get("content", "").strip()
    if not content:
        return Response({"detail": "Message cannot be empty."}, status=400)
    reply_to_id = request.data.get("reply_to") or request.data.get("replyToId")
    reply_to = BookClubMessage.objects.filter(pk=reply_to_id, club_id=club_id).first() if reply_to_id else None
    message = BookClubMessage.objects.create(club_id=club_id, sender=request.user, content=content[:3000], reply_to=reply_to)
    payload = message_payload(message)
    broadcast_club_event(club_id, {"type": "insert", "message": payload})
    if reply_to:
        notify(reply_to.sender, request.user, "book_club_reply", book_club_id=club_id, event_key=f"book-club-reply:{message.pk}")
    return Response(BookClubMessageSerializer(message, context={"request": request}).data, status=201)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def message_detail(request, club_id, message_id):
    message = BookClubMessage.objects.filter(pk=message_id, club_id=club_id).select_related("sender").first()
    if not message:
        return Response({"detail": "Message not found."}, status=404)
    membership = get_member(club_id, request.user)
    if message.sender_id != request.user.pk and not can_moderate(membership):
        return Response({"detail": "You cannot delete this message."}, status=403)
    message_id = message.pk
    message.delete()
    broadcast_club_event(club_id, {"type": "delete", "message": {"id": message_id}})
    return Response(status=204)


@api_view(["POST", "PATCH"])
@permission_classes([IsAuthenticated])
def pin_message(request, club_id, message_id):
    if not can_moderate(get_member(club_id, request.user)):
        return Response({"detail": "Only a club owner or admin can pin messages."}, status=403)
    message = BookClubMessage.objects.filter(pk=message_id, club_id=club_id).select_related("sender__profile").first()
    if not message:
        return Response({"detail": "Message not found."}, status=404)
    message.is_pinned = bool(request.data.get("pinned", request.data.get("isPinned", not message.is_pinned)))
    message.save(update_fields=["is_pinned"])
    payload = message_payload(message)
    broadcast_club_event(club_id, {"type": "update", "message": payload})
    return Response(BookClubMessageSerializer(message, context={"request": request}).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def club_resources(request, club_id):
    member = get_member(club_id, request.user)
    if not member:
        return Response({"detail": "Join this Book Club to view its resources."}, status=403)
    if request.method == "GET":
        query = BookClubResource.objects.filter(club_id=club_id).select_related("resource__author__profile")
        return Response(BookClubResourceSerializer(query, many=True, context={"request": request}).data)
    if member.role not in {"owner", "admin"}:
        return Response({"detail": "Only a club owner or admin can add resources."}, status=403)
    serializer = BookClubResourceCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    resource = serializer.validated_data["resource"]
    link, created = BookClubResource.objects.get_or_create(club_id=club_id, resource=resource, defaults={"added_by": request.user})
    data = BookClubResourceSerializer(link, context={"request": request}).data
    data["created"] = created
    return Response(data, status=201 if created else 200)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def club_resource_detail(request, club_id, resource_id):
    member = get_member(club_id, request.user)
    if not member or member.role not in {"owner", "admin"}:
        return Response({"detail": "Only a club owner or admin can remove resources."}, status=403)
    # Delete only this join row; the library resource remains intact.
    BookClubResource.objects.filter(club_id=club_id, resource_id=resource_id).delete()
    return Response({"removed": True})

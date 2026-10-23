import re

from allauth.account.models import EmailAddress
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
from django.db.models import Subquery
from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils.text import slugify
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from config.storage_backends import media_storage_available_for_upload
from .models import Follow, Notification, Profile, notify
from .serializers import NotificationSerializer, ProfileSerializer

User = get_user_model()

def public_user_count(request):
    """Public, read-only page showing the current registered-user total."""
    return render(request, "user.html", {"user_count": User.objects.count()})



@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_token(request):
    return Response({"csrfToken": get_token(request)})


def user_data(user, request):
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={"username": slugify(user.username)[:30] or f"reader-{user.pk}", "display_name": user.get_full_name()},
    )
    return {
        "id": user.pk,
        "email": user.email,
        "user_metadata": {"display_name": profile.display_name, "avatar_url": profile.avatar_url},
        "profile": ProfileSerializer(profile, context={"request": request}).data,
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def current_user(request):
    if not request.user.is_authenticated:
        return Response({"user": None})
    return Response({"user": user_data(request.user, request)})


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    email = request.data.get("email", "").strip().lower()
    password = request.data.get("password", "")
    display_name = request.data.get("display_name", "").strip()[:80]
    if not email or not password:
        return Response({"detail": "Email and password are required."}, status=400)
    try:
        validate_email(email)
        validate_password(password)
    except ValidationError as error:
        return Response({"detail": " ".join(error.messages)}, status=400)
    if User.objects.filter(email__iexact=email).exists():
        return Response({"detail": "An account with this email already exists."}, status=400)
    base = slugify(email.split("@", 1)[0])[:24] or "reader"
    username = base
    suffix = 1
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f"{base[:24]}-{suffix}"
    try:
        user = User.objects.create_user(username=username, email=email, password=password, first_name=display_name)
        Profile.objects.update_or_create(user=user, defaults={"username": username, "display_name": display_name})
        address = EmailAddress.objects.add_email(request, user, email, confirm=True, signup=True)
        if not address.primary:
            address.primary = True
            address.save(update_fields=["primary"])
    except IntegrityError:
        return Response({"detail": "Unable to create an account with those details."}, status=400)
    login(request, user)
    return Response({"user": user_data(user, request)}, status=201)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get("email", "").strip().lower()
    password = request.data.get("password", "")
    user_obj = User.objects.filter(email__iexact=email).first()
    user = authenticate(request, username=user_obj.username, password=password) if user_obj else None
    if not user:
        return Response({"detail": "Email or password is incorrect."}, status=400)
    login(request, user)
    return Response({"user": user_data(user, request)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({"detail": "Signed out."})


@api_view(["POST"])
@permission_classes([AllowAny])
def resend_verification(request):
    email = request.data.get("email", "").strip().lower()
    address = EmailAddress.objects.filter(email__iexact=email, verified=False).select_related("user").first()
    if address:
        address.send_confirmation(request, signup=True)
    return Response({"detail": "If the address needs verification, a message has been sent."})


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset(request):
    form = PasswordResetForm({"email": request.data.get("email", "")})
    if not form.is_valid():
        return Response({"detail": "Enter a valid email address."}, status=400)
    form.save(
        request=request,
        use_https=request.is_secure(),
        email_template_name="registration/password_reset_email.html",
        subject_template_name="registration/password_reset_subject.txt",
        extra_email_context={"frontend_url": request.data.get("frontend_url", "http://localhost:5173")},
    )
    return Response({"detail": "If an account exists for that email, a reset message has been sent."})


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    try:
        user_id = urlsafe_base64_decode(request.data.get("uid", "")).decode()
        user = User.objects.get(pk=user_id)
    except (ValueError, TypeError, User.DoesNotExist):
        return Response({"detail": "This reset link is invalid or expired."}, status=400)
    token = request.data.get("token", "")
    password = request.data.get("password", "")
    if not default_token_generator.check_token(user, token):
        return Response({"detail": "This reset link is invalid or expired."}, status=400)
    try:
        validate_password(password, user)
    except Exception as error:
        return Response({"detail": str(error)}, status=400)
    user.set_password(password)
    user.save(update_fields=["password"])
    return Response({"detail": "Password updated. You can sign in now."})


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def my_profile(request):
    profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={"username": slugify(request.user.username)[:30] or f"reader-{request.user.pk}"},
    )
    if request.method == "GET":
        return Response(ProfileSerializer(profile, context={"request": request}).data)
    avatar = request.FILES.get("avatar")
    if avatar and (not (avatar.content_type or "").startswith("image/") or avatar.size > 5 * 1024 * 1024):
        return Response({"detail": "Choose an image smaller than 5 MB."}, status=400)
    if avatar and not media_storage_available_for_upload():
        return Response({"detail": "Cloudflare R2 media storage is not configured."}, status=503)
    serializer = ProfileSerializer(profile, data=request.data, partial=True, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def users(request):
    query = request.query_params.get("q", "").strip()
    profiles = Profile.objects.select_related("user").all()
    if request.query_params.get("suggested") == "1":
        import random

        if request.user.is_authenticated:
            followed_ids = Follow.objects.filter(follower=request.user).values("following_id")
            profiles = profiles.exclude(user=request.user).exclude(user_id__in=Subquery(followed_ids))
        candidates = list(profiles.order_by("-created_at")[:60])
        random.shuffle(candidates)
        return Response(ProfileSerializer(candidates[:12], many=True, context={"request": request}).data)
    if query:
        from django.db.models import Q
        profiles = profiles.filter(Q(username__icontains=query) | Q(display_name__icontains=query) | Q(bio__icontains=query))
    return Response(ProfileSerializer(profiles[:30], many=True, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def user_detail(request, user_id):
    profile = Profile.objects.select_related("user").filter(user_id=user_id).first()
    if not profile:
        return Response({"detail": "Profile not found."}, status=404)
    return Response(ProfileSerializer(profile, context={"request": request}).data)


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def follow_user(request, user_id):
    target = User.objects.filter(pk=user_id).first()
    if not target:
        return Response({"detail": "User not found."}, status=404)
    if target == request.user:
        return Response({"detail": "You cannot follow yourself."}, status=400)
    if request.method == "POST":
        follow, created = Follow.objects.get_or_create(follower=request.user, following=target)
        if created:
            notify(target, request.user, "follow", event_key=f"follow:{follow.pk}")
    else:
        Follow.objects.filter(follower=request.user, following=target).delete()
    return Response({"following": request.method == "POST"})


def _follow_list(request, user_id, incoming):
    target = User.objects.filter(pk=user_id).first()
    if not target:
        return Response({"detail": "User not found."}, status=404)
    edges = Follow.objects.filter(following=target if incoming else None) if incoming else Follow.objects.filter(follower=target)
    if incoming:
        edges = edges.select_related("follower__profile")
        profiles = [edge.follower.profile for edge in edges if hasattr(edge.follower, "profile")]
    else:
        edges = edges.select_related("following__profile")
        profiles = [edge.following.profile for edge in edges if hasattr(edge.following, "profile")]
    return Response(ProfileSerializer(profiles, many=True, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def user_followers(request, user_id):
    return _follow_list(request, user_id, True)


@api_view(["GET"])
@permission_classes([AllowAny])
def user_following(request, user_id):
    return _follow_list(request, user_id, False)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notifications(request):
    queryset = Notification.objects.filter(recipient=request.user).select_related("actor__profile")
    unread_only = request.query_params.get("unread") == "true"
    if unread_only:
        queryset = queryset.filter(read=False)
    return Response(NotificationSerializer(queryset[:100], many=True, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def unread_notification_count(request):
    return Response({"count": Notification.objects.filter(recipient=request.user, read=False).count()})


@api_view(["POST", "PATCH"])
@permission_classes([IsAuthenticated])
def notification_read(request, notification_id):
    notification = Notification.objects.filter(pk=notification_id, recipient=request.user).first()
    if not notification:
        return Response({"detail": "Notification not found."}, status=404)
    notification.read = True
    notification.save(update_fields=["read"])
    from messaging.realtime import send_user_event
    send_user_event(request.user.pk, {"type": "notification_count", "count": Notification.objects.filter(recipient=request.user, read=False).count()})
    return Response({"read": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def notification_read_all(request):
    Notification.objects.filter(recipient=request.user, read=False).update(read=True)
    from messaging.realtime import send_user_event
    send_user_event(request.user.pk, {"type": "notification_count", "count": 0})
    return Response({"read": True})


@api_view(["GET", "POST", "DELETE"])
@permission_classes([IsAuthenticated])
def push_subscriptions(request):
    from .models import PushSubscription

    if request.method == "GET":
        return Response({"subscribed": PushSubscription.objects.filter(user=request.user).exists()})

    endpoint = request.data.get("endpoint", "")
    if request.method == "DELETE":
        if not isinstance(endpoint, str):
            return Response({"detail": "A valid push endpoint is required."}, status=400)
        PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
        return Response({"subscribed": False})

    from urllib.parse import urlparse

    if not isinstance(endpoint, str) or not endpoint or len(endpoint) > 2048:
        return Response({"detail": "A valid browser push subscription is required."}, status=400)
    try:
        parsed = urlparse(endpoint)
    except ValueError:
        return Response({"detail": "This push service endpoint is not supported."}, status=400)
    allowed_hosts = (
        "fcm.googleapis.com",
        "push.services.mozilla.com",
        "push.apple.com",
        "notify.windows.com",
    )
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host or parsed.username or parsed.password or not any(
        host == allowed or host.endswith("." + allowed) for allowed in allowed_hosts
    ):
        return Response({"detail": "This push service endpoint is not supported."}, status=400)

    keys = request.data.get("keys") or {}
    p256dh = keys.get("p256dh", "") if isinstance(keys, dict) else ""
    auth = keys.get("auth", "") if isinstance(keys, dict) else ""
    if (
        not isinstance(p256dh, str)
        or not isinstance(auth, str)
        or not p256dh
        or not auth
        or len(p256dh) > 200
        or len(auth) > 100
    ):
        return Response({"detail": "A valid browser push subscription is required."}, status=400)
    import hashlib

    endpoint_hash = hashlib.sha256(endpoint.encode("utf-8")).hexdigest()
    existing = PushSubscription.objects.filter(endpoint_hash=endpoint_hash).first()
    if existing and existing.user_id != request.user.pk:
        return Response({"detail": "This browser subscription is already linked to another account."}, status=409)
    PushSubscription.objects.update_or_create(
        endpoint_hash=endpoint_hash,
        defaults={"user": request.user, "endpoint": endpoint, "p256dh": p256dh, "auth": auth},
    )
    return Response({"subscribed": True}, status=201)


@api_view(["GET"])
@permission_classes([AllowAny])
def push_public_key(request):
    from django.conf import settings

    if not (settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY and settings.VAPID_SUBJECT):
        return Response({"enabled": False, "public_key": ""})
    return Response({"enabled": True, "public_key": settings.VAPID_PUBLIC_KEY})

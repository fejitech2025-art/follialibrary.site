import re

from allauth.account.models import EmailAddress
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils.text import slugify
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Follow, Notification, Profile, notify
from .serializers import NotificationSerializer, ProfileSerializer

User = get_user_model()


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
    serializer = ProfileSerializer(profile, data=request.data, partial=True, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def users(request):
    query = request.query_params.get("q", "").strip()
    profiles = Profile.objects.select_related("user").all()
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
        _, created = Follow.objects.get_or_create(follower=request.user, following=target)
        if created:
            notify(target, request.user, "follow")
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


@api_view(["POST", "PATCH"])
@permission_classes([IsAuthenticated])
def notification_read(request, notification_id):
    notification = Notification.objects.filter(pk=notification_id, recipient=request.user).first()
    if not notification:
        return Response({"detail": "Notification not found."}, status=404)
    notification.read = True
    notification.save(update_fields=["read"])
    return Response({"read": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def notification_read_all(request):
    Notification.objects.filter(recipient=request.user, read=False).update(read=True)
    return Response({"read": True})

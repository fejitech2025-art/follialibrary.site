from django.db.models import Q
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from accounts.models import Follow, notify
from accounts.models import Profile
from accounts.serializers import ProfileSerializer
from config.storage_backends import media_storage_available_for_upload
from library.models import Resource, ResourceComment, ResourceCommentLike
from library.serializers import ResourceSerializer
from clubs.models import BookClub
from clubs.serializers import BookClubSerializer
from .models import ContentReport, Post, PostBookmark, PostComment, PostCommentLike, PostLike
from .serializers import PostCommentSerializer, PostSerializer
from config.watermark import WatermarkProcessingError, watermarked_download

MAX_POST_VIDEO_SIZE = 40 * 1024 * 1024


def visible_posts(request):
    query = Post.objects.select_related("author__profile").prefetch_related("likes", "comments", "bookmarks", "media_items")
    if request.user.is_authenticated:
        # Keep a public feed simple in v1; following state is returned for the creator affordance.
        return query
    return query


@api_view(["GET"])
@permission_classes([AllowAny])
def feed(request):
    items = []
    post_query = visible_posts(request)
    resource_query = Resource.objects.filter(status="published").select_related("author__profile").prefetch_related("likes", "comments", "bookmarks")
    if request.user.is_authenticated and request.query_params.get("tab") == "following":
        followed_ids = Follow.objects.filter(follower=request.user).values_list("following_id", flat=True)
        post_query = post_query.filter(Q(author_id__in=followed_ids) | Q(author=request.user))
        resource_query = resource_query.filter(Q(author_id__in=followed_ids) | Q(author=request.user))
    for post in post_query[:50]:
        data = PostSerializer(post, context={"request": request}).data
        items.append({"kind": "post", **data})
    for resource in resource_query[:50]:
        data = ResourceSerializer(resource, context={"request": request}).data
        items.append({"kind": "resource", **data, "author": data["profiles"], "body": resource.description})
    items.sort(key=lambda item: item["created_at"], reverse=True)
    return Response(items[:60])


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def posts(request):
    if request.method == "GET":
        query = visible_posts(request)
        author = request.query_params.get("author")
        if author:
            query = query.filter(author_id=author)
        return Response(PostSerializer(query[:60], many=True, context={"request": request}).data)
    if not request.user.is_authenticated:
        return Response({"detail": "Sign in to publish a post."}, status=401)
    body = request.data.get("body", "").strip()
    uploads = request.FILES.getlist("media")
    if not uploads and request.FILES.get("media"):
        uploads = [request.FILES.get("media")]
    if not body and not uploads:
        return Response({"detail": "Add text or an image/video to your post."}, status=400)
    if len(body) > 5000:
        return Response({"detail": "Posts can be up to 5,000 characters."}, status=400)
    upload_error = validate_post_uploads(uploads)
    if upload_error:
        return Response({"detail": upload_error}, status=400)
    if uploads and not media_storage_available_for_upload():
        return Response({"detail": "Cloudflare R2 media storage is not configured."}, status=503)
    media_type = uploaded_media_type(uploads[0]) if uploads else ""
    if uploads and media_type == "video":
        post = Post.objects.create(author=request.user, body=body, media=uploads[0], media_type="video")
    elif len(uploads) == 1:
        post = Post.objects.create(author=request.user, body=body, media=uploads[0], media_type="image")
    else:
        post = Post.objects.create(author=request.user, body=body, media_type="image")
        for position, upload in enumerate(uploads):
            post.media_items.create(file=upload, media_type="image", position=position)
    return Response(PostSerializer(post, context={"request": request}).data, status=201)


def validate_post_uploads(uploads):
    if any(not ((upload.content_type or "").startswith("image/") or uploaded_media_type(upload) == "video") for upload in uploads):
        return "Post media must be an image or video."
    videos = [upload for upload in uploads if uploaded_media_type(upload) == "video"]
    if videos and len(uploads) > 1:
        return "Attach one video at a time. Videos cannot be combined with other media."
    if videos and videos[0].size > MAX_POST_VIDEO_SIZE:
        return "Videos must be 40 MB or smaller."
    if any(uploaded_media_type(upload) != "video" and upload.size > 50 * 1024 * 1024 for upload in uploads):
        return "Post images must be 50 MB or smaller."
    return ""


def uploaded_media_type(upload):
    if (upload.content_type or "").lower().startswith("video/"):
        return "video"
    try:
        header = upload.read(16)
        upload.seek(0)
    except (OSError, AttributeError):
        header = b""
    if header.startswith((b"\x1a\x45\xdf\xa3", b"OggS")) or (header[:4] == b"RIFF" and header[8:12] == b"AVI ") or header[4:8] == b"ftyp" or header.startswith(b"\x00\x00\x01\xba"):
        return "video"
    return "image" if (upload.content_type or "").lower().startswith("image/") else ""


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def saved_posts(request):
    bookmarks = PostBookmark.objects.filter(user=request.user).select_related("post__author__profile")
    return Response([
        {"id": item.pk, "created_at": item.created_at, "kind": "post", "posts": PostSerializer(item.post, context={"request": request}).data}
        for item in bookmarks
    ])


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([AllowAny])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def post_detail(request, post_id):
    post = visible_posts(request).filter(pk=post_id).first()
    if not post:
        return Response({"detail": "Post not found."}, status=404)
    if request.method == "GET":
        return Response(PostSerializer(post, context={"request": request}).data)
    if not request.user.is_authenticated or post.author_id != request.user.pk:
        return Response({"detail": "Only the creator can edit or remove this post."}, status=403)
    if request.method == "DELETE":
        post.delete()
        return Response(status=204)
    uploads = request.FILES.getlist("media")
    if not uploads and request.FILES.get("media"):
        uploads = [request.FILES.get("media")]
    upload_error = validate_post_uploads(uploads)
    if upload_error:
        return Response({"detail": upload_error}, status=400)
    if uploads and not media_storage_available_for_upload():
        return Response({"detail": "Cloudflare R2 media storage is not configured."}, status=503)
    serializer_data = request.data
    if len(uploads) > 1:
        serializer_data = request.data.copy()
        serializer_data.pop("media", None)
        serializer_data.pop("media_type", None)
    serializer = PostSerializer(post, data=serializer_data, partial=True, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    if len(uploads) > 1:
        if post.media:
            post.media.delete(save=False)
        post.media = ""
        post.media_type = "image"
        post.save(update_fields=["media", "media_type"])
        for existing in post.media_items.all():
            existing.file.delete(save=False)
            existing.delete()
        for position, upload in enumerate(uploads):
            post.media_items.create(file=upload, media_type="image", position=position)
    elif uploads:
        for existing in post.media_items.all():
            existing.file.delete(save=False)
            existing.delete()
    return Response(serializer.data)


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def post_like(request, post_id):
    post = Post.objects.filter(pk=post_id).select_related("author").first()
    if not post:
        return Response({"detail": "Post not found."}, status=404)
    if request.method == "POST":
        like, created = PostLike.objects.get_or_create(user=request.user, post=post)
        if created:
            notify(post.author, request.user, "like", post_id=post.pk, event_key=f"post-like:{like.pk}")
        liked = True
    else:
        PostLike.objects.filter(user=request.user, post=post).delete()
        liked = False
    return Response({"liked": liked, "count": post.likes.count()})


@api_view(["GET"])
@permission_classes([AllowAny])
def post_media_file(request, post_id, media_id=None):
    post = Post.objects.select_related("author__profile").filter(pk=post_id).first()
    if not post:
        return Response({"detail": "Post not found."}, status=404)
    if media_id is not None:
        item = post.media_items.filter(pk=media_id).first()
        field = item.file if item else None
        filename = item.file.name.rsplit("/", 1)[-1] if item else ""
    elif post.media:
        field = post.media
        filename = post.media.name.rsplit("/", 1)[-1]
    else:
        item = post.media_items.first()
        field = item.file if item else None
        filename = item.file.name.rsplit("/", 1)[-1] if item else ""
    if not field:
        return Response({"detail": "Post media not found."}, status=404)
    try:
        media_type = item.media_type if media_id is not None and item else post.media_type
        supplied_type = "video/mp4" if media_type == "video" else ""
        return watermarked_download(field, filename, post.author.profile.username, supplied_type)
    except WatermarkProcessingError as error:
        return Response({"detail": str(error)}, status=503)
    except Exception:
        return Response({"detail": "This media could not be prepared for download."}, status=422)


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def post_comment_like(request, post_id, comment_id):
    comment = PostComment.objects.select_related("user", "post").filter(pk=comment_id, post_id=post_id).first()
    if not comment:
        return Response({"detail": "Comment not found."}, status=404)
    if request.method == "POST":
        like, created = PostCommentLike.objects.get_or_create(user=request.user, comment=comment)
        if created:
            notify(
                comment.user,
                request.user,
                "comment_like",
                post_id=post_id,
                comment_id=comment.pk,
                event_key=f"post-comment-like:{comment.pk}:{request.user.pk}",
            )
        liked = True
    else:
        PostCommentLike.objects.filter(user=request.user, comment=comment).delete()
        liked = False
    return Response({"liked": liked, "count": comment.likes.count()})


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def post_save(request, post_id):
    post = Post.objects.filter(pk=post_id).first()
    if not post:
        return Response({"detail": "Post not found."}, status=404)
    if request.method == "POST":
        PostBookmark.objects.get_or_create(user=request.user, post=post)
        return Response({"saved": True})
    PostBookmark.objects.filter(user=request.user, post=post).delete()
    return Response({"saved": False})


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def post_comments(request, post_id):
    post = Post.objects.filter(pk=post_id).first()
    if not post:
        return Response({"detail": "Post not found."}, status=404)
    if request.method == "GET":
        comments = post.comments.filter(parent__isnull=True).select_related("user__profile").prefetch_related("replies__user__profile")[:100]
        return Response(PostCommentSerializer(comments, many=True, context={"request": request}).data)
    if not request.user.is_authenticated:
        return Response({"detail": "Sign in to comment."}, status=401)
    serializer = PostCommentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    parent_id = request.data.get("parent_id")
    parent = None
    if parent_id not in (None, ""):
        try:
            parent_id = int(parent_id)
        except (TypeError, ValueError):
            return Response({"detail": "Invalid comment to reply to."}, status=400)
        parent = PostComment.objects.filter(
            pk=parent_id, post=post, parent__isnull=True
        ).select_related("user").first()
        if not parent:
            return Response({"detail": "Comment to reply to was not found for this post."}, status=400)
    comment = serializer.save(user=request.user, post=post, parent=parent)
    if parent:
        notify(
            parent.user,
            request.user,
            "comment_reply",
            post_id=post.pk,
            event_key=f"post-comment-reply:{comment.pk}",
        )
    else:
        notify(
            post.author,
            request.user,
            "comment",
            post_id=post.pk,
            event_key=f"post-comment:{comment.pk}",
        )
    return Response(PostCommentSerializer(comment, context={"request": request}).data, status=201)


def _create_report(request, **target):
    reason = request.data.get("reason", "other")
    description = request.data.get("description", "")
    allowed_reasons = {value for value, _ in ContentReport.REASON_CHOICES}
    if reason not in allowed_reasons:
        return Response({"detail": "Choose a valid report reason."}, status=400)
    if not isinstance(description, str):
        return Response({"detail": "Report explanation must be text."}, status=400)
    description = description.strip()
    if len(description) > 500:
        return Response({"detail": "Report explanations can be up to 500 characters."}, status=400)
    existing = ContentReport.objects.filter(reporter=request.user, **target).first()
    if existing:
        return Response({"reported": True, "duplicate": True}, status=200)
    ContentReport.objects.create(reporter=request.user, reason=reason, description=description, **target)
    return Response({"reported": True, "duplicate": False}, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def report_post(request, post_id):
    post = Post.objects.filter(pk=post_id).first()
    if not post:
        return Response({"detail": "Post not found."}, status=404)
    return _create_report(request, post=post)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def report_user(request, user_id):
    profile = Profile.objects.filter(user_id=user_id).select_related("user").first()
    if not profile:
        return Response({"detail": "Profile not found."}, status=404)
    return _create_report(request, reported_user=profile.user)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def report_post_comment(request, post_id, comment_id):
    comment = PostComment.objects.filter(pk=comment_id, post_id=post_id).first()
    if not comment:
        return Response({"detail": "Comment not found."}, status=404)
    return _create_report(request, post_comment=comment)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def report_resource(request, resource_id):
    resource = Resource.objects.filter(pk=resource_id, status="published").first()
    if not resource:
        return Response({"detail": "Resource not found."}, status=404)
    return _create_report(request, resource=resource)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def report_resource_comment(request, resource_id, comment_id):
    comment = ResourceComment.objects.filter(pk=comment_id, resource_id=resource_id, resource__status="published").first()
    if not comment:
        return Response({"detail": "Comment not found."}, status=404)
    return _create_report(request, resource_comment=comment)


@api_view(["GET"])
@permission_classes([AllowAny])
def search(request):
    query = request.query_params.get("q", "").strip()
    if not query:
        return Response({"users": [], "posts": [], "resources": [], "clubs": []})
    users = Profile.objects.select_related("user").filter(Q(username__icontains=query) | Q(display_name__icontains=query) | Q(bio__icontains=query))[:12]
    posts_query = Post.objects.select_related("author__profile").filter(Q(body__icontains=query))[:20]
    resources_query = Resource.objects.filter(status="published").select_related("author__profile").filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(category__icontains=query) | Q(language__icontains=query))[:20]
    clubs_query = BookClub.objects.select_related("owner__profile").filter(Q(name__icontains=query) | Q(description__icontains=query))[:12]
    return Response({
        "users": ProfileSerializer(users, many=True, context={"request": request}).data,
        "posts": PostSerializer(posts_query, many=True, context={"request": request}).data,
        "resources": ResourceSerializer(resources_query, many=True, context={"request": request}).data,
        "clubs": BookClubSerializer(clubs_query, many=True, context={"request": request}).data,
    })

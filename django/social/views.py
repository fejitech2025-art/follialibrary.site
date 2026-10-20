from django.db.models import Q
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from accounts.models import Follow, notify
from accounts.models import Profile
from accounts.serializers import ProfileSerializer
from config.storage_backends import media_storage_available_for_upload
from library.models import Resource
from library.serializers import ResourceSerializer
from clubs.models import BookClub
from clubs.serializers import BookClubSerializer
from .models import ContentReport, Post, PostBookmark, PostComment, PostLike
from .serializers import PostCommentSerializer, PostSerializer


def visible_posts(request):
    query = Post.objects.select_related("author__profile").prefetch_related("likes", "comments", "bookmarks")
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
    media = request.FILES.get("media")
    if not body and not media:
        return Response({"detail": "Add text or an image/video to your post."}, status=400)
    if len(body) > 5000:
        return Response({"detail": "Posts can be up to 5,000 characters."}, status=400)
    if media and (not (media.content_type or "").startswith(("image/", "video/")) or media.size > 50 * 1024 * 1024):
        return Response({"detail": "Post media must be an image or video smaller than 50 MB."}, status=400)
    if media and not media_storage_available_for_upload():
        return Response({"detail": "Cloudflare R2 media storage is not configured."}, status=503)
    media_type = request.data.get("media_type", "")
    if media and media_type not in {"image", "video"}:
        media_type = "video" if (media.content_type or "").startswith("video/") else "image"
    post = Post.objects.create(author=request.user, body=body, media=media or "", media_type=media_type)
    return Response(PostSerializer(post, context={"request": request}).data, status=201)


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
    media = request.FILES.get("media")
    if media and (not (media.content_type or "").startswith(("image/", "video/")) or media.size > 50 * 1024 * 1024):
        return Response({"detail": "Post media must be an image or video smaller than 50 MB."}, status=400)
    if media and not media_storage_available_for_upload():
        return Response({"detail": "Cloudflare R2 media storage is not configured."}, status=503)
    serializer = PostSerializer(post, data=request.data, partial=True, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def report_post(request, post_id):
    post = Post.objects.filter(pk=post_id).first()
    if not post:
        return Response({"detail": "Post not found."}, status=404)
    ContentReport.objects.get_or_create(
        reporter=request.user,
        post=post,
        defaults={"reason": request.data.get("reason", "other"), "description": request.data.get("description", "")[:500]},
    )
    return Response({"reported": True}, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def report_user(request, user_id):
    profile = Profile.objects.filter(user_id=user_id).select_related("user").first()
    if not profile:
        return Response({"detail": "Profile not found."}, status=404)
    ContentReport.objects.get_or_create(
        reporter=request.user,
        reported_user=profile.user,
        defaults={"reason": request.data.get("reason", "other"), "description": request.data.get("description", "")[:500]},
    )
    return Response({"reported": True}, status=201)


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

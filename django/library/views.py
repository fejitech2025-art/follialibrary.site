from django.db.models import Q
from django.http import FileResponse
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from accounts.models import notify
from .models import Resource, ResourceBookmark, ResourceComment, ResourceLike
from .serializers import ResourceCommentSerializer, ResourceSerializer


def find_resource(resource_id, request):
    query = Resource.objects.select_related("author__profile")
    if request.user.is_authenticated:
        query = query.filter(Q(status="published") | Q(author=request.user))
    else:
        query = query.filter(status="published")
    return query.filter(pk=resource_id).first()


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def resources(request):
    if request.method == "GET":
        query = Resource.objects.filter(status="published").select_related("author__profile")
        author_id = request.query_params.get("author")
        category = request.query_params.get("category")
        if author_id:
            query = query.filter(author_id=author_id)
        if category and category.lower() != "all":
            query = query.filter(category__iexact=category)
        search = request.query_params.get("q", "").strip()
        if search:
            query = query.filter(Q(title__icontains=search) | Q(description__icontains=search) | Q(category__icontains=search))
        return Response(ResourceSerializer(query[:60], many=True, context={"request": request}).data)
    if not request.user.is_authenticated:
        return Response({"detail": "Sign in to upload a resource."}, status=401)
    upload = request.FILES.get("file")
    cover = request.FILES.get("cover")
    if upload and upload.size > 50 * 1024 * 1024:
        return Response({"detail": "Resource files must be 50 MB or smaller."}, status=400)
    if cover and (not (cover.content_type or "").startswith("image/") or cover.size > 5 * 1024 * 1024):
        return Response({"detail": "Cover images must be images smaller than 5 MB."}, status=400)
    payload = request.data.copy()
    if "tags" in payload and isinstance(payload["tags"], str):
        payload["tags"] = [tag.strip() for tag in payload["tags"].split(",") if tag.strip()]
    payload["status"] = payload.get("status", "published")
    serializer = ResourceSerializer(data=payload, context={"request": request})
    serializer.is_valid(raise_exception=True)
    resource = serializer.save(author=request.user)
    if resource.file and not resource.file_name:
        resource.file_name = resource.file.name.rsplit("/", 1)[-1]
        resource.file_type = request.FILES.get("file").content_type if request.FILES.get("file") else ""
        resource.save(update_fields=["file_name", "file_type"])
    return Response(ResourceSerializer(resource, context={"request": request}).data, status=201)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([AllowAny])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def resource_detail(request, resource_id):
    resource = find_resource(resource_id, request)
    if not resource:
        return Response({"detail": "Resource not found."}, status=404)
    if request.method == "GET":
        return Response(ResourceSerializer(resource, context={"request": request}).data)
    if not request.user.is_authenticated or resource.author_id != request.user.pk:
        return Response({"detail": "Only the creator can edit this resource."}, status=403)
    if request.method == "DELETE":
        if resource.file:
            resource.file.delete(save=False)
        if resource.cover:
            resource.cover.delete(save=False)
        resource.delete()
        return Response(status=204)
    upload = request.FILES.get("file")
    cover = request.FILES.get("cover")
    if upload and upload.size > 50 * 1024 * 1024:
        return Response({"detail": "Resource files must be 50 MB or smaller."}, status=400)
    if cover and (not (cover.content_type or "").startswith("image/") or cover.size > 5 * 1024 * 1024):
        return Response({"detail": "Cover images must be images smaller than 5 MB."}, status=400)
    payload = request.data.copy()
    if "tags" in payload and isinstance(payload["tags"], str):
        payload["tags"] = [tag.strip() for tag in payload["tags"].split(",") if tag.strip()]
    serializer = ResourceSerializer(resource, data=payload, partial=True, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def resource_like(request, resource_id):
    resource = Resource.objects.filter(pk=resource_id, status="published").first()
    if not resource:
        return Response({"detail": "Resource not found."}, status=404)
    if request.method == "POST":
        _, created = ResourceLike.objects.get_or_create(user=request.user, resource=resource)
        if created:
            notify(resource.author, request.user, "like", resource_id=resource.pk)
        liked = True
    else:
        ResourceLike.objects.filter(user=request.user, resource=resource).delete()
        liked = False
    return Response({"liked": liked, "count": resource.likes.count()})


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def resource_save(request, resource_id):
    resource = Resource.objects.filter(pk=resource_id, status="published").first()
    if not resource:
        return Response({"detail": "Resource not found."}, status=404)
    if request.method == "POST":
        ResourceBookmark.objects.get_or_create(user=request.user, resource=resource)
        return Response({"saved": True})
    ResourceBookmark.objects.filter(user=request.user, resource=resource).delete()
    return Response({"saved": False})


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def resource_comments(request, resource_id):
    resource = Resource.objects.filter(pk=resource_id, status="published").first()
    if not resource:
        return Response({"detail": "Resource not found."}, status=404)
    if request.method == "GET":
        comments = resource.comments.select_related("user__profile")[:100]
        return Response(ResourceCommentSerializer(comments, many=True, context={"request": request}).data)
    if not request.user.is_authenticated:
        return Response({"detail": "Sign in to comment."}, status=401)
    serializer = ResourceCommentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    comment = serializer.save(user=request.user, resource=resource)
    notify(resource.author, request.user, "comment", resource_id=resource.pk)
    return Response(ResourceCommentSerializer(comment, context={"request": request}).data, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def bookmarks(request):
    saved = ResourceBookmark.objects.filter(user=request.user).select_related("resource__author__profile")
    data = [{"id": item.pk, "created_at": item.created_at, "resource_id": item.resource_id, "kind": "resource", "resources": ResourceSerializer(item.resource, context={"request": request}).data} for item in saved]
    return Response(data)


@api_view(["GET"])
@permission_classes([AllowAny])
def resource_file(request, resource_id):
    resource = Resource.objects.filter(pk=resource_id).first()
    if not resource or not resource.file:
        return Response({"detail": "Resource file not found."}, status=404)
    if not resource.is_free and (not request.user.is_authenticated or request.user != resource.author):
        return Response({"detail": "This resource is not available for free download."}, status=403)
    return FileResponse(resource.file.open("rb"), as_attachment=True, filename=resource.file_name or resource.file.name.rsplit("/", 1)[-1])

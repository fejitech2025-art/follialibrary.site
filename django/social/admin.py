from django.contrib import admin
from django.utils.html import format_html

from django.conf import settings
from .models import ContentReport, Post, PostBookmark, PostComment, PostCommentLike, PostLike, PostMedia

admin.site.register(Post)
@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "post", "created_at")
    search_fields = ("content", "user__username", "post__body")


@admin.register(PostMedia)
class PostMediaAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "media_type", "position", "created_at")


@admin.register(PostCommentLike)
class PostCommentLikeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "comment", "created_at")


@admin.register(ContentReport)
class ContentReportAdmin(admin.ModelAdmin):
    list_display = ("id", "target_link", "reporter", "reported_user", "reason", "status", "created_at")
    list_filter = ("status", "reason", "created_at")
    search_fields = ("reporter__username", "reported_user__username", "description", "post__body", "post_comment__content", "resource__title", "resource_comment__content")
    readonly_fields = ("reporter", "post", "post_comment", "resource", "resource_comment", "reported_user", "reason", "description", "created_at", "target_link")
    fields = ("target_link", "post", "post_comment", "resource", "resource_comment", "reported_user", "reporter", "reason", "description", "created_at", "status")

    @admin.display(description="Reported item")
    def target_link(self, obj):
        if obj.post_id:
            path = f"/post/{obj.post_id}"
        elif obj.post_comment_id:
            path = f"/post/{obj.post_comment.post_id}"
        elif obj.resource_id:
            path = f"/resource/{obj.resource_id}"
        elif obj.resource_comment_id:
            path = f"/resource/{obj.resource_comment.resource_id}"
        elif obj.reported_user_id:
            path = f"/profile/{obj.reported_user_id}"
        else:
            return "—"
        return format_html('<a href="{}" target="_blank" rel="noopener">Open in Follia Library</a>', settings.FOLLIA_PUBLIC_URL.rstrip("/") + path)


admin.site.register(PostLike)
admin.site.register(PostBookmark)

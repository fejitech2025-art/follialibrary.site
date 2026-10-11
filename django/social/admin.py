from django.contrib import admin

from .models import ContentReport, Post, PostBookmark, PostComment, PostLike

admin.site.register(Post)
admin.site.register(PostComment)
admin.site.register(PostLike)
admin.site.register(PostBookmark)
admin.site.register(ContentReport)

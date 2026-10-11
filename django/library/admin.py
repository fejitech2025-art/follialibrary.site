from django.contrib import admin

from .models import Resource, ResourceBookmark, ResourceComment, ResourceLike

admin.site.register(Resource)
admin.site.register(ResourceBookmark)
admin.site.register(ResourceComment)
admin.site.register(ResourceLike)

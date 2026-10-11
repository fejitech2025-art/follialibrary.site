from django.contrib import admin

from .models import Follow, Notification, Profile

admin.site.register(Profile)
admin.site.register(Follow)
admin.site.register(Notification)

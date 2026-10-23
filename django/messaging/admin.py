from django.contrib import admin

from .models import Conversation, DirectMessage, MessageReport, UserBlock


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "user_one", "user_two", "created_at", "updated_at")
    search_fields = ("user_one__username", "user_two__username")


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "message_type", "created_at")
    list_filter = ("message_type", "created_at")
    search_fields = ("body", "sender__username")
    readonly_fields = ("client_id", "created_at", "read_at")


@admin.register(UserBlock)
class UserBlockAdmin(admin.ModelAdmin):
    list_display = ("blocker", "blocked", "created_at")
    search_fields = ("blocker__username", "blocked__username")


@admin.register(MessageReport)
class MessageReportAdmin(admin.ModelAdmin):
    list_display = ("id", "reporter", "message", "reason", "created_at")
    list_filter = ("reason", "created_at")
    search_fields = ("reporter__username", "description", "message__body")
    readonly_fields = ("reporter", "message", "reason", "description", "created_at")

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from accounts import views as account_views
from clubs import views as club_views
from library import views as library_views
from social import views as social_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("users/", account_views.public_user_count, name="public-user-count"),
    path("accounts/", include("allauth.urls")),
    path("api/auth/csrf/", account_views.csrf_token, name="csrf-token"),
    path("api/auth/me/", account_views.current_user, name="current-user"),
    path("api/auth/logout/", account_views.logout_view, name="logout-api"),
    path("api/me/profile/", account_views.my_profile, name="my-profile"),
    path("api/users/", account_views.users, name="users"),
    path("api/users/<int:user_id>/", account_views.user_detail, name="user-detail"),
    path("api/users/<int:user_id>/follow/", account_views.follow_user, name="follow-user"),
    path("api/users/<int:user_id>/report/", social_views.report_user, name="report-user"),
    path("api/users/<int:user_id>/followers/", account_views.user_followers, name="user-followers"),
    path("api/users/<int:user_id>/following/", account_views.user_following, name="user-following"),
    path("api/feed/", social_views.feed, name="feed"),
    path("api/posts/", social_views.posts, name="posts"),
    path("api/bookmarks/posts/", social_views.saved_posts, name="saved-posts"),
    path("api/posts/<int:post_id>/", social_views.post_detail, name="post-detail"),
    path("api/posts/<int:post_id>/like/", social_views.post_like, name="post-like"),
    path("api/posts/<int:post_id>/file/", social_views.post_media_file, name="post-media-file"),
    path("api/posts/<int:post_id>/media/<int:media_id>/file/", social_views.post_media_file, name="post-media-item-file"),
    path("api/posts/<int:post_id>/save/", social_views.post_save, name="post-save"),
    path("api/posts/<int:post_id>/comments/", social_views.post_comments, name="post-comments"),
    path("api/posts/<int:post_id>/comments/<int:comment_id>/like/", social_views.post_comment_like, name="post-comment-like"),
    path("api/posts/<int:post_id>/comments/<int:comment_id>/report/", social_views.report_post_comment, name="report-post-comment"),
    path("api/posts/<int:post_id>/report/", social_views.report_post, name="report-post"),
    path("api/resources/", library_views.resources, name="resources"),
    path("api/resources/<int:resource_id>/", library_views.resource_detail, name="resource-detail"),
    path("api/resources/<int:resource_id>/like/", library_views.resource_like, name="resource-like"),
    path("api/resources/<int:resource_id>/save/", library_views.resource_save, name="resource-save"),
    path("api/resources/<int:resource_id>/comments/", library_views.resource_comments, name="resource-comments"),
    path("api/resources/<int:resource_id>/comments/<int:comment_id>/like/", library_views.resource_comment_like, name="resource-comment-like"),
    path("api/resources/<int:resource_id>/comments/<int:comment_id>/report/", social_views.report_resource_comment, name="report-resource-comment"),
    path("api/resources/<int:resource_id>/file/", library_views.resource_file, name="resource-file"),
    path("api/resources/<int:resource_id>/preview/", library_views.resource_preview, name="resource-preview"),
    path("api/resources/<int:resource_id>/report/", social_views.report_resource, name="report-resource"),
    path("api/bookmarks/", library_views.bookmarks, name="bookmarks"),
    path("api/search/", social_views.search, name="search"),
    path("api/notifications/", account_views.notifications, name="notifications"),
    path("api/notifications/unread-count/", account_views.unread_notification_count, name="unread-notification-count"),
    path("api/notifications/<int:notification_id>/read/", account_views.notification_read, name="notification-read"),
    path("api/notifications/read-all/", account_views.notification_read_all, name="notification-read-all"),
    path("api/push/public-key/", account_views.push_public_key, name="push-public-key"),
    path("api/push/subscriptions/", account_views.push_subscriptions, name="push-subscriptions"),
    path("api/clubs/", club_views.clubs, name="clubs"),
    path("api/clubs/<int:club_id>/", club_views.club_detail, name="club-detail"),
    path("api/clubs/<int:club_id>/membership/", club_views.club_membership, name="club-membership"),
    path("api/clubs/<int:club_id>/join/", club_views.join_club, name="join-club"),
    path("api/clubs/<int:club_id>/members/<int:member_id>/", club_views.manage_member, name="manage-member"),
    path("api/clubs/<int:club_id>/messages/", club_views.messages, name="club-messages"),
    path("api/clubs/<int:club_id>/messages/<int:message_id>/", club_views.message_detail, name="club-message-detail"),
    path("api/clubs/<int:club_id>/messages/<int:message_id>/pin/", club_views.pin_message, name="pin-message"),
    path("api/clubs/<int:club_id>/resources/", club_views.club_resources, name="club-resources"),
    path("api/clubs/<int:club_id>/resources/<int:resource_id>/", club_views.club_resource_detail, name="club-resource-detail"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

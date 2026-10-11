from django.contrib import admin

from .models import BookClub, BookClubMembership, BookClubMessage, BookClubResource

admin.site.register(BookClub)
admin.site.register(BookClubMembership)
admin.site.register(BookClubMessage)
admin.site.register(BookClubResource)

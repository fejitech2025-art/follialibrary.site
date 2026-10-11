from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class FolliaAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        from django.conf import settings

        return settings.LOGIN_REDIRECT_URL


class FolliaSocialAccountAdapter(DefaultSocialAccountAdapter):
    pass

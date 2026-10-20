from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.utils.text import slugify


class FolliaAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        from django.conf import settings

        return settings.LOGIN_REDIRECT_URL


class FolliaSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if user.username and not get_user_model().objects.filter(username=user.username).exists():
            return user

        source = data.get("email", "").split("@", 1)[0] or data.get("name", "reader")
        base = slugify(source)[:24] or "reader"
        candidate = base
        suffix = 1
        User = get_user_model()
        while User.objects.filter(username=candidate).exists():
            suffix += 1
            candidate = f"{base[:24 - len(str(suffix)) - 1]}-{suffix}"
        user.username = candidate
        return user

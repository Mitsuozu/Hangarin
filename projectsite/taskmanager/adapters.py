"""Controls who may create an account.

Hangarin's tasks are shared (they are not tied to a user), so by default nobody
can sign up on their own: accounts are created by an admin, and each person
connects Google / GitHub to their existing account from Settings.
Set HANGARIN_SOCIAL_SIGNUP = True to let Google / GitHub logins create an
account automatically, and HANGARIN_OPEN_SIGNUP = True to also allow the
username + password sign up form.
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings


def _open():
    return getattr(settings, "HANGARIN_OPEN_SIGNUP", False)


def _social_open():
    return getattr(settings, "HANGARIN_SOCIAL_SIGNUP", False) or _open()


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return _open()


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return _social_open()

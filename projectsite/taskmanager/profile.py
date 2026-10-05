from allauth.socialaccount.models import SocialAccount


def profile_for(user):
    """Display name, photo and initial for a signed-in user.

    Name: the name saved on the account, else the one from Google / GitHub,
    else the username. Photo: from a connected Google / GitHub account.
    """
    name = user.get_full_name().strip()
    avatar_url = ""
    for account in SocialAccount.objects.filter(user=user).order_by("id"):
        if not name:
            name = (account.extra_data.get("name") or "").strip()
        if not avatar_url:
            avatar_url = account.get_avatar_url() or ""
    name = name or user.get_username()
    return {
        "name": name,
        "first_name": name.split()[0] if name else "",
        "avatar_url": avatar_url,
        "initial": name[:1].upper() or "?",
    }

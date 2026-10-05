from django.conf import settings
from django.utils import timezone

from .models import Task
from .profile import profile_for


def hangarin_globals(request):
    """Values every Hangarin page needs (navbar bell + overdue checks)."""
    now = timezone.now()
    overdue_count = 0
    profile = None
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        profile = profile_for(user)
        overdue_count = Task.objects.filter(deadline__lt=now).exclude(status="Completed").count()
    return {
        "now": now,
        "overdue_count": overdue_count,
        "profile": profile,
        "open_signup": getattr(settings, "HANGARIN_OPEN_SIGNUP", False),
    }

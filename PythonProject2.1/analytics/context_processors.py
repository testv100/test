from .roles import is_manager, is_teacher

def role_flags(request):
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        return {
            "is_manager": is_manager(user),
            "is_teacher": is_teacher(user),
        }
    return {"is_manager": False, "is_teacher": False}
from .models import Notification

def notifications_badge(request):
    if not request.user.is_authenticated:
        return {"notif_unread": 0}

    from .models import Notification  # импорт внутри, безопасно

    return {
        "notif_unread": Notification.objects.filter(user=request.user, is_read=False).count()
    }

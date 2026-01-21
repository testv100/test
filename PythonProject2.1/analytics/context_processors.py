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

    from .models import Notification

    return {
        "notif_unread": Notification.objects.filter(user=request.user, is_read=False).count()
    }
from django.contrib.auth.models import Group

def role_context(request):

    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"is_manager": False, "is_teacher": False}

    is_manager = user.is_staff or user.is_superuser
    is_teacher = user.groups.filter(name="Преподаватели").exists()

    return {"is_manager": is_manager, "is_teacher": is_teacher}
def unread_notifications(request):
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        return {"unread_notifications": user.notifications.filter(is_read=False).count()}
    return {"unread_notifications": 0}
from django.db.utils import OperationalError, ProgrammingError

def unread_notifications(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"unread_notifications": 0}

    try:
        return {"unread_notifications": user.notifications.filter(is_read=False).count()}
    except (OperationalError, ProgrammingError):
        # Таблица ещё не создана / миграции не применены
        return {"unread_notifications": 0}

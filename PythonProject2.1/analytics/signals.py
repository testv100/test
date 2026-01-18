from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Result, Notification

User = get_user_model()

def _get_recipients_for_grade():
    # просто: уведомляем всех админов/менеджеров + всех преподавателей
    users = []
    for u in User.objects.all():
        try:
            if is_manager(u) or is_teacher(u):
                users.append(u)
        except Exception:
            pass
    return users

@receiver(post_save, sender=Result)
def notify_new_grade(sender, instance: Result, created: bool, **kwargs):
    if not created:
        return

    st = getattr(instance, "student", None)
    dis = getattr(instance, "discipline", None)
    sem = getattr(instance, "semester", None)

    sem_txt = f"{sem.year}/{sem.term}" if sem else "-"
    title = "Добавлена новая оценка"
    message = f"{st.full_name if st else '-'} • {dis.name if dis else '-'} • семестр {sem_txt}"

    for u in _get_recipients_for_grade():
        Notification.objects.create(
            user=u,
            type=Notification.TYPE_GRADE,
            title=title,
            message=message,
        )

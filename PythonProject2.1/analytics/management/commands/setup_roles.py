from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User

class Command(BaseCommand):
    help = "Create roles/groups and demo users"

    def handle(self, *args, **kwargs):
        admin_g, _ = Group.objects.get_or_create(name="Администратор")
        head_g, _ = Group.objects.get_or_create(name="Руководитель кафедры")
        teacher_g, _ = Group.objects.get_or_create(name="Преподаватель")

        p_upload = Permission.objects.get(codename="can_upload_csv")
        p_teacher = Permission.objects.get(codename="can_view_teacher")
        p_dept = Permission.objects.get(codename="can_view_department")

        admin_g.permissions.set([p_upload, p_teacher, p_dept])
        head_g.permissions.set([p_dept])
        teacher_g.permissions.set([p_teacher])

        def upsert(username, password, group, is_staff=False, is_superuser=False):
            u, _ = User.objects.get_or_create(username=username)
            u.is_staff = is_staff
            u.is_superuser = is_superuser
            u.set_password(password)   # критично: иначе пароль не хэшируется
            u.save()
            u.groups.set([group])

        upsert("admin", "Admin12345!", admin_g, is_staff=True, is_superuser=True)
        upsert("head", "Head12345!", head_g)
        upsert("teacher", "Teacher12345!", teacher_g)

        self.stdout.write(self.style.SUCCESS("Roles/users created or updated."))

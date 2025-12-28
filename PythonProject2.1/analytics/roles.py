def is_teacher(user):
    return bool(user and user.is_authenticated and user.groups.filter(name='Преподаватель').exists())


def is_manager(user):
    if not user or not user.is_authenticated:
        return False
    # учтём формулировку из замечаний: "Руководитель кафедры"
    return user.is_superuser or user.groups.filter(
        name__in=['Руководитель', 'Руководитель кафедры', 'Администратор']
    ).exists()


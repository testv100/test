from django.db import models
from django.conf import settings
from django.utils import timezone

class Feedback(models.Model):
    name = models.CharField("Имя", max_length=120)
    email = models.EmailField("Email", blank=True)
    message = models.TextField("Сообщение")
    created_at = models.DateTimeField("Дата", auto_now_add=True)
    is_processed = models.BooleanField("Обработано", default=False)

    class Meta:
        verbose_name = "Обратная связь"
        verbose_name_plural = "Обратная связь"

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} — {self.name}"

class Notification(models.Model):
    TYPE_GRADE = "grade"
    TYPE_REPORT = "report"
    TYPE_CHOICES = [
        (TYPE_GRADE, "Новая оценка"),
        (TYPE_REPORT, "Сформирован отчёт"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.title}"


class News(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=True)

    is_pinned = models.BooleanField("Закрепить (важная)", default=False)
    image = models.ImageField("Превью", upload_to="news/", blank=True, null=True)

    source = models.CharField(max_length=50, blank=True)
    source_url = models.URLField(blank=True, unique=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class RolePermissions(models.Model):
    class Meta:
        managed = False
        permissions = [
            ("can_upload_csv", "Can upload CSV"),
            ("can_view_teacher", "Can view teacher analytics"),
            ("can_view_department", "Can view department analytics"),
        ]


class Group(models.Model):
    name = models.CharField(max_length=50)
    program = models.CharField(max_length=100, blank=True)
    year = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name


class Discipline(models.Model):
    name = models.CharField(max_length=200)
    department = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name


class Teacher(models.Model):
    full_name = models.CharField(max_length=200)
    department = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.full_name


class Semester(models.Model):
    year = models.IntegerField()
    term = models.CharField(max_length=20)

    def __str__(self):
        return f'{self.term} {self.year}'


class Student(models.Model):
    full_name = models.CharField(max_length=200)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='students')

    def __str__(self):
        return self.full_name


class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results', verbose_name='Студент')
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, related_name='results',
                                   verbose_name='Дисциплина')
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='results',
                                verbose_name='Преподаватель')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='results', verbose_name='Семестр')
    grade = models.FloatField(verbose_name='Оценка')
    attendance_percent = models.FloatField(default=0, verbose_name='Посещаемость (%)')

    class Meta:
        verbose_name = 'Результат'
        verbose_name_plural = 'Результаты'
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'discipline', 'teacher', 'semester'],
                name='uniq_result_student_discipline_teacher_semester'
            )
        ]

    def __str__(self):
        return f'{self.student} – {self.discipline} – {self.grade}'


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('upload', 'Загрузка данных'),
        ('export_csv', 'Экспорт CSV'),
        ('export_pdf', 'Экспорт PDF'),
        ('login', 'Вход'),
        ('logout', 'Выход'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Пользователь',
    )
    action = models.CharField('Действие', max_length=20, choices=ACTION_CHOICES)
    created_at = models.DateTimeField('Время', auto_now_add=True)
    details = models.TextField('Подробности', blank=True)

    class Meta:
        verbose_name = 'Журнал действий'
        verbose_name_plural = 'Журнал действий'

    def __str__(self):
        return f"{self.get_action_display()} ({self.created_at:%Y-%m-%d %H:%M})"


class TeacherUserLink(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_link',
        verbose_name='Пользователь'
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='user_links',
        verbose_name='Преподаватель'
    )


    class Meta:
        verbose_name = 'Привязка преподавателя к пользователю'
        verbose_name_plural = 'Привязки преподавателей к пользователям'


    def __str__(self):
        return f'{self.user} → {self.teacher}'
class ImportBatch(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="import_batches",
        verbose_name="Пользователь",
    )
    file_name = models.CharField("Файл", max_length=255)
    created_at = models.DateTimeField("Дата", auto_now_add=True)

    total_rows = models.PositiveIntegerField("Строк всего", default=0)
    created_results = models.PositiveIntegerField("Создано записей", default=0)
    updated_results = models.PositiveIntegerField("Обновлено записей", default=0)
    error_rows = models.PositiveIntegerField("Ошибок", default=0)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Импорт CSV"
        verbose_name_plural = "Импорты CSV"

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} — {self.file_name}"


class ImportRowError(models.Model):
    batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.CASCADE,
        related_name="errors",
        verbose_name="Партия импорта",
    )
    row_number = models.PositiveIntegerField("Номер строки")
    raw_row = models.TextField("Данные строки", blank=True)
    error = models.TextField("Ошибка")

    class Meta:
        ordering = ["row_number"]
        verbose_name = "Ошибка импорта"
        verbose_name_plural = "Ошибки импорта"

    def __str__(self):
        return f"Строка {self.row_number}"
print("NEWS MODEL LOADED")

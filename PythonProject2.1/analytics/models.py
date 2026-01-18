from django.db import models
from django.conf import settings
from django.utils import timezone


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

    source = models.CharField(max_length=50, blank=True)
    source_url = models.URLField(blank=True, unique=True)

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
    term = models.CharField(max_length=20)  # например: "Осень 2025"

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
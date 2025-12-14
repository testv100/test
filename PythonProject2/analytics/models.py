from django.db import models
from django.conf import settings

# Create your models here.
from django.db import models


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
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, related_name='results')
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='results')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='results')
    grade = models.FloatField()
    attendance_percent = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Результат'
        verbose_name_plural = 'Результаты'

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

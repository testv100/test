from django.contrib import admin
from .models import Group, Discipline, Teacher, Semester, Student, Result


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'program', 'year')


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ('name', 'department')


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'department')


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('year', 'term')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'group')
    list_filter = ('group',)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'discipline', 'semester', 'grade', 'attendance_percent')
    list_filter = ('discipline', 'semester', 'student__group')
from django.contrib import admin
from .models import AuditLog  # + остальные модели, если уже есть

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action')
    list_filter = ('action', 'created_at')
    search_fields = ('details',)


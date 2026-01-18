# analytics/admin.py
from django.contrib import admin
from .models import (
    AuditLog,
    Discipline,
    Group,
    News,
    Result,
    Semester,
    Student,
    Teacher,
    TeacherUserLink,
)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'program', 'year')  # ДОБАВЬТЕ 'program', 'year'
    search_fields = ('name',)
    # Поля 'program' и 'year' теперь присутствуют в модели

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'group')
    list_filter = ('group',)
    search_fields = ('full_name',)

@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'discipline', 'teacher', 'semester', 'grade', 'attendance_percent')
    list_filter = ('semester', 'discipline', 'teacher')
    search_fields = ('student__full_name',)

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name')

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('id', 'year', 'term')
    list_filter = ('year', 'term')

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'is_published', 'created_at', 'source')
    list_filter = ('is_published', 'source')
    search_fields = ('title', 'body')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'action', 'created_at')
    list_filter = ('action', 'created_at')
    readonly_fields = ('user', 'action', 'details', 'created_at')

@admin.register(TeacherUserLink)
class TeacherUserLinkAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'teacher')
    search_fields = ('user__username', 'teacher__full_name')
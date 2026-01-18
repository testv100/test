# analytics/urls.py
from django.urls import path
from analytics import views

app_name = "analytics"

urlpatterns = [
    # Главная
    path("", views.home, name="home"),

    # Регистрация
    path("register/", views.register, name="register"),

    # Основное
    path("dashboard/", views.dashboard, name="dashboard"),

    # Инфо-страницы
    path("info/<slug:slug>/", views.info, name="info"),

    # Группы
    path("groups/<int:group_id>/", views.group_detail, name="group_detail"),
    path("groups/<int:group_id>/profile/", views.group_profile, name="group_profile"),

    # Дисциплины
    path("disciplines/<int:discipline_id>/", views.discipline_detail, name="discipline_detail"),

    # Экспорт
    path("export/pdf/", views.export_pdf, name="export_pdf"),
    path("export/csv/", views.export_results, name="export_results"),

    # Импорт
    path("upload/", views.upload_results, name="upload_results"),

    # Новости (публичная)
    path("news/<int:pk>/", views.news_detail, name="news_detail"),

    # Новости (управление)
    path("admin/news/", views.news_admin_list, name="news_admin_list"),
    path("admin/news/create/", views.news_admin_create, name="news_admin_create"),
    path("admin/news/<int:pk>/edit/", views.news_admin_edit, name="news_admin_edit"),
    path("admin/news/<int:pk>/delete/", views.news_admin_delete, name="news_admin_delete"),
    path("admin/news/<int:pk>/toggle/", views.news_admin_toggle_publish, name="news_admin_toggle_publish"),

    # Администрирование
    path("audit/", views.audit_log, name="audit_log"),
    path("teacher-links/", views.teacher_links, name="teacher_links"),
]
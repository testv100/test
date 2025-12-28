from django.urls import path

from . import views


app_name = "analytics"


urlpatterns = [
    # Корень сайта
    path("", views.home, name="home"),

    # Основная панель
    path("dashboard/", views.dashboard, name="dashboard"),

    # Детализация
    path("group/<int:group_id>/", views.group_detail, name="group_detail"),
    path("group/<int:group_id>/profile/", views.group_profile, name="group_profile"),
    path("discipline/<int:discipline_id>/", views.discipline_detail, name="discipline_detail"),

    # Импорт/экспорт (доступ зависит от роли)
    path("upload/", views.upload_results, name="upload_results"),
    path("export/results/", views.export_results, name="export_results"),
    path("export/pdf/", views.export_pdf, name="export_pdf"),

    # Служебные страницы (только руководители)
    path("audit/", views.audit_log, name="audit_log"),
    path("teacher-links/", views.teacher_links, name="teacher_links"),
    path("teacher-links/<int:link_id>/delete/", views.teacher_link_delete, name="teacher_link_delete"),

    # API
    path("api/summary/", views.api_summary, name="api_summary"),
]

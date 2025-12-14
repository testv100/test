from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('group/<int:group_id>/', views.group_detail, name='group_detail'),
    path('group/<int:group_id>/profile/', views.group_profile, name='group_profile'),
    path('discipline/<int:discipline_id>/', views.discipline_detail, name='discipline_detail'),
    path('upload/', views.upload_results, name='upload_results'),
    path('export/results/', views.export_results, name='export_results'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
]
path('api/summary/', views.api_summary, name='api_summary'),

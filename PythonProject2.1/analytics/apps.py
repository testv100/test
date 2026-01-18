
from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analytics'

    # Не регистрируйте модели здесь
    # def ready(self):
    #     import analytics.signals  # если есть сигналы
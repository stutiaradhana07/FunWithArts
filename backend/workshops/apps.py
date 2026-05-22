from django.apps import AppConfig


class WorkshopsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workshops'

    def ready(self):
        import notifications.signals  # noqa: F401 — wire email signals

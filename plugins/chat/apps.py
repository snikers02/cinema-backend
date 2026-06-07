from django.apps import AppConfig

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins.chat'

    def ready(self):
        import plugins.signals  # noqa: F401
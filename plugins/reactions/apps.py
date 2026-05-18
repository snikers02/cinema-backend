from django.apps import AppConfig


class ReactionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins.reactions'

    def ready(self):
        import plugins.reactions.signals
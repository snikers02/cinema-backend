from django.apps import AppConfig

class AchievementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins.achievements'

    def ready(self):
        import plugins.achievements.signals

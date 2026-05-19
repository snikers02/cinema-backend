from django.apps import AppConfig


class MoviesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins.movies'

    def ready(self):
        print("!!! MoviesConfig ready() called, importing signals !!!")
        import plugins.movies.signals
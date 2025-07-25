from django.apps import AppConfig


class ThefoodConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'thefood'

    def ready(self):
        import thefood.signals

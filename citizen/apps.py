from django.apps import AppConfig

class CitizenConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'citizen'

    def ready(self):
        import citizen.signals

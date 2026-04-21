from django.apps import AppConfig


class TecnicosConfig(AppConfig):
    default_auto_field = "django_mongodb_backend.fields.ObjectIdAutoField"
    name = "apps.tecnicos"
    
    def ready(self):
        from . import signals  # noqa: F401

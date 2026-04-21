from django.apps import AppConfig


class ClientesConfig(AppConfig):
    default_auto_field = "django_mongodb_backend.fields.ObjectIdAutoField"
    name = "apps.clientes"
    
    def ready(self):
        from . import signals  # noqa: F401

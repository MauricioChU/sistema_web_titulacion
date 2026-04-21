from django.apps import AppConfig


class InventarioConfig(AppConfig):
    default_auto_field = "django_mongodb_backend.fields.ObjectIdAutoField"
    name = "apps.inventario"

    def ready(self):
        from . import signals  # noqa: F401

from django.apps import AppConfig


class PedidosConfig(AppConfig):
    default_auto_field = "django_mongodb_backend.fields.ObjectIdAutoField"
    name = "apps.pedidos"

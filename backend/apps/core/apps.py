from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "apps.core"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        from apps.core.db import init_indexes
        try:
            init_indexes()
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("MongoDB index init failed: %s", exc)

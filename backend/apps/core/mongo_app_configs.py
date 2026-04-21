from django.contrib.admin.apps import AdminConfig
from django.contrib.auth.apps import AuthConfig
from django.contrib.contenttypes.apps import ContentTypesConfig
from django.contrib.sessions.apps import SessionsConfig
from django.db.models.signals import post_migrate

from django.contrib.auth.management import create_permissions

from .auth_permissions import create_permissions_safe


_OBJECT_ID_AUTO_FIELD = "django_mongodb_backend.fields.ObjectIdAutoField"


class MongoAdminConfig(AdminConfig):
    default_auto_field = _OBJECT_ID_AUTO_FIELD


class MongoAuthConfig(AuthConfig):
    default_auto_field = _OBJECT_ID_AUTO_FIELD

    def ready(self):
        super().ready()
        post_migrate.disconnect(
            dispatch_uid="django.contrib.auth.management.create_permissions"
        )
        post_migrate.connect(
            create_permissions_safe,
            dispatch_uid="django.contrib.auth.management.create_permissions",
        )


class MongoContentTypesConfig(ContentTypesConfig):
    default_auto_field = _OBJECT_ID_AUTO_FIELD


class MongoSessionsConfig(SessionsConfig):
    default_auto_field = _OBJECT_ID_AUTO_FIELD

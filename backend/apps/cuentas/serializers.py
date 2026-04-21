from apps.core.serializers import MongoModelSerializer
from .models import Cuenta


class CuentaSerializer(MongoModelSerializer):
    class Meta:
        model = Cuenta
        fields = "__all__"

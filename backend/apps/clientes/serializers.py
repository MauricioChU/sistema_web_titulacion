from apps.core.serializers import MongoModelSerializer
from .models import Cliente


class ClienteSerializer(MongoModelSerializer):
    class Meta:
        model = Cliente
        fields = "__all__"

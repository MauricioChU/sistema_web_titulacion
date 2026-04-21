from apps.core.serializers import MongoModelSerializer
from .models import Tecnico


class TecnicoSerializer(MongoModelSerializer):
    class Meta:
        model = Tecnico
        fields = "__all__"

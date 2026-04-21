from apps.core.serializers import MongoModelSerializer

from .models import ItemInventario


class ItemInventarioSerializer(MongoModelSerializer):
    class Meta:
        model = ItemInventario
        fields = "__all__"

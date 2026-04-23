from rest_framework import serializers

from .models import ItemInventario


class ItemInventarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemInventario
        fields = [
            "id",
            "sku",
            "descripcion",
            "categoria",
            "stock",
            "stock_minimo",
            "unidad_medida",
            "almacen",
            "activo",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

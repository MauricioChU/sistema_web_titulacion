from rest_framework import serializers

from .models import Cuenta


class CuentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cuenta
        fields = [
            "id",
            "cliente",
            "nombre",
            "numero",
            "direccion",
            "distrito",
            "contacto",
            "telefono",
            "tipo",
            "latitud",
            "longitud",
            "activa",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

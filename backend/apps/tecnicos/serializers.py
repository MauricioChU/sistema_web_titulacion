from rest_framework import serializers

from .models import Tecnico


class TecnicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tecnico
        fields = [
            "id",
            "user",
            "nombre",
            "especialidad",
            "zona",
            "latitud_base",
            "longitud_base",
            "capacidad_diaria",
            "activo",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

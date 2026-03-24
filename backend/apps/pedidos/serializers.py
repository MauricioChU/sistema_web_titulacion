from rest_framework import serializers
from .models import Pedido


class PedidoSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True)
    tecnico_nombre = serializers.CharField(source="tecnico_asignado.nombre", read_only=True)

    class Meta:
        model = Pedido
        fields = "__all__"

    def validate(self, attrs):
        cliente = attrs.get("cliente") or getattr(self.instance, "cliente", None)
        cuenta = attrs.get("cuenta") if "cuenta" in attrs else getattr(self.instance, "cuenta", None)

        if cuenta and cliente and cuenta.cliente_id != cliente.id:
            raise serializers.ValidationError({
                "cuenta": "La cuenta seleccionada no pertenece al cliente del pedido."
            })

        return attrs

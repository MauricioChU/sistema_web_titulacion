from rest_framework import serializers

from .models import ChecklistStep, Evidencia, InformeTecnico, Pedido, TecnicoUpdate


class TecnicoUpdateSerializer(serializers.ModelSerializer):
    tecnico_nombre = serializers.CharField(source="tecnico.nombre", read_only=True, default="")

    class Meta:
        model = TecnicoUpdate
        fields = [
            "id",
            "pedido",
            "tecnico",
            "tecnico_nombre",
            "nota",
            "nuevo_estado",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "tecnico_nombre"]


class ChecklistStepSerializer(serializers.ModelSerializer):
    tecnico_nombre = serializers.CharField(source="tecnico.nombre", read_only=True, default="")

    class Meta:
        model = ChecklistStep
        fields = [
            "id",
            "pedido",
            "tecnico",
            "tecnico_nombre",
            "step_id",
            "completado",
            "nota",
            "completado_en",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "tecnico_nombre", "completado_en"]
        extra_kwargs = {
            "pedido": {"required": False},
            "tecnico": {"required": False},
        }


class EvidenciaSerializer(serializers.ModelSerializer):
    tecnico_nombre = serializers.CharField(source="tecnico.nombre", read_only=True, default="")

    class Meta:
        model = Evidencia
        fields = [
            "id",
            "pedido",
            "tecnico",
            "tecnico_nombre",
            "nombre",
            "archivo",
            "descripcion",
            "stage",
            "source",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "tecnico_nombre"]


class InformeTecnicoSerializer(serializers.ModelSerializer):
    tecnico_nombre = serializers.CharField(source="tecnico.nombre", read_only=True, default="")

    class Meta:
        model = InformeTecnico
        fields = [
            "id",
            "pedido",
            "tecnico",
            "tecnico_nombre",
            "diagnostico_final",
            "responsable_local",
            "pedido_solicitado",
            "observaciones",
            "recomendaciones",
            "firma_cliente",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "tecnico_nombre"]


class PedidoSerializer(serializers.ModelSerializer):
    """Forma que consume el frontend (campos planos cuenta_/cliente_/tecnico_)."""

    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True, default="")
    cuenta_numero = serializers.CharField(source="cuenta.numero", read_only=True, default="")
    cuenta_nombre = serializers.CharField(source="cuenta.nombre", read_only=True, default="")
    cuenta_direccion = serializers.CharField(source="cuenta.direccion", read_only=True, default="")
    cuenta_distrito = serializers.CharField(source="cuenta.distrito", read_only=True, default="")
    cuenta_latitud = serializers.FloatField(source="cuenta.latitud", read_only=True, default=None)
    cuenta_longitud = serializers.FloatField(source="cuenta.longitud", read_only=True, default=None)
    tecnico_nombre = serializers.CharField(source="tecnico_asignado.nombre", read_only=True, default="")

    tecnico_updates = TecnicoUpdateSerializer(many=True, read_only=True)
    checklist_steps = ChecklistStepSerializer(many=True, read_only=True)
    evidencias = EvidenciaSerializer(many=True, read_only=True)
    informe_tecnico = InformeTecnicoSerializer(read_only=True)

    class Meta:
        model = Pedido
        fields = [
            "id",
            "codigo",
            "cliente",
            "cuenta",
            "tecnico_asignado",
            "titulo",
            "descripcion",
            "tipo_servicio",
            "zona",
            "prioridad",
            "fase",
            "status_operativo",
            "subfase_tecnica",
            "diagnostico_tecnico",
            "historial",
            "fecha_programada",
            "fecha_inicio_labor",
            "fecha_fin_labor",
            "fecha_cierre",
            "created_at",
            "updated_at",
            # Campos planos para el front
            "cliente_nombre",
            "cuenta_numero",
            "cuenta_nombre",
            "cuenta_direccion",
            "cuenta_distrito",
            "cuenta_latitud",
            "cuenta_longitud",
            "tecnico_nombre",
            # Relaciones anidadas
            "tecnico_updates",
            "checklist_steps",
            "evidencias",
            "informe_tecnico",
        ]
        read_only_fields = [
            "codigo",
            "historial",
            "created_at",
            "updated_at",
            "tecnico_updates",
            "checklist_steps",
            "evidencias",
            "informe_tecnico",
            "cliente_nombre",
            "cuenta_numero",
            "cuenta_nombre",
            "cuenta_direccion",
            "cuenta_distrito",
            "cuenta_latitud",
            "cuenta_longitud",
            "tecnico_nombre",
        ]

    def validate(self, attrs):
        cliente = attrs.get("cliente") or getattr(self.instance, "cliente", None)
        cuenta = attrs.get("cuenta") if "cuenta" in attrs else getattr(self.instance, "cuenta", None)

        if cuenta and cliente and cuenta.cliente_id != cliente.id:
            raise serializers.ValidationError(
                {"cuenta": "La cuenta seleccionada no pertenece al cliente del pedido."}
            )
        return attrs

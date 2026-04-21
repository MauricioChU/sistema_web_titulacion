from rest_framework import serializers
from apps.core.serializers import MongoModelSerializer
from .models import ChecklistStep, Evidencia, InformeTecnico, Pedido, TecnicoUpdate


class TecnicoUpdateSerializer(MongoModelSerializer):
    tecnico_nombre = serializers.CharField(source="tecnico.nombre", read_only=True)

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


class ChecklistStepSerializer(MongoModelSerializer):
    tecnico_nombre = serializers.CharField(source="tecnico.nombre", read_only=True)

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

    def validate(self, attrs):
        step_id = attrs.get("step_id")
        nota = (attrs.get("nota") or "").strip()
        if step_id == ChecklistStep.StepId.NOTA_ADICIONAL and not nota:
            raise serializers.ValidationError({"nota": "La nota adicional es obligatoria para este paso."})
        return attrs


class EvidenciaSerializer(MongoModelSerializer):
    tecnico_nombre = serializers.CharField(source="tecnico.nombre", read_only=True)

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


class InformeTecnicoSerializer(MongoModelSerializer):
    tecnico_nombre = serializers.CharField(source="tecnico.nombre", read_only=True)

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


class PedidoSerializer(MongoModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True)
    cuenta_numero = serializers.CharField(source="cuenta.numero", read_only=True)
    cuenta_nombre = serializers.CharField(source="cuenta.nombre", read_only=True)
    cuenta_direccion = serializers.CharField(source="cuenta.direccion", read_only=True)
    cuenta_distrito = serializers.CharField(source="cuenta.distrito", read_only=True)
    cuenta_latitud = serializers.FloatField(source="cuenta.latitud", read_only=True)
    cuenta_longitud = serializers.FloatField(source="cuenta.longitud", read_only=True)
    tecnico_nombre = serializers.CharField(source="tecnico_asignado.nombre", read_only=True)
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
            "cliente_nombre",
            "cuenta_numero",
            "cuenta_nombre",
            "cuenta_direccion",
            "cuenta_distrito",
            "cuenta_latitud",
            "cuenta_longitud",
            "tecnico_nombre",
            "tecnico_updates",
            "checklist_steps",
            "evidencias",
            "informe_tecnico",
        ]
        read_only_fields = [
            "codigo",
            "created_at",
            "updated_at",
            "tecnico_updates",
            "checklist_steps",
            "evidencias",
            "informe_tecnico",
            "cuenta_numero",
            "cuenta_nombre",
            "cuenta_direccion",
            "cuenta_distrito",
            "cuenta_latitud",
            "cuenta_longitud",
        ]

    def validate(self, attrs):
        cliente = attrs.get("cliente") or getattr(self.instance, "cliente", None)
        cuenta = attrs.get("cuenta") if "cuenta" in attrs else getattr(self.instance, "cuenta", None)

        if cuenta and cliente and cuenta.cliente_id != cliente.id:
            raise serializers.ValidationError({
                "cuenta": "La cuenta seleccionada no pertenece al cliente del pedido."
            })

        return attrs

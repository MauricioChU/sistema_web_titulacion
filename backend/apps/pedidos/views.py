from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.recomendaciones.services import recomendar_tecnico_para_pedido
from .mongo_sync import delete_pedido_from_mongo, sync_pedido_to_mongo
from .models import ChecklistStep, Evidencia, InformeTecnico, Pedido, TecnicoUpdate
from .serializers import (
    ChecklistStepSerializer,
    EvidenciaSerializer,
    InformeTecnicoSerializer,
    PedidoSerializer,
)


class PedidoViewSet(ModelViewSet):
    queryset = Pedido.objects.select_related("cliente", "cuenta", "tecnico_asignado").prefetch_related(
        "tecnico_updates", "checklist_steps", "evidencias", "informe_tecnico"
    )
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = [
        "fase",
        "prioridad",
        "cliente",
        "cuenta",
        "tecnico_asignado",
        "zona",
        "tipo_servicio",
        "status_operativo",
        "subfase_tecnica",
    ]
    search_fields = [
        "titulo",
        "descripcion",
        "diagnostico_tecnico",
        "cliente__nombre",
        "cuenta__nombre",
        "tecnico_asignado__nombre",
    ]
    ordering_fields = ["created_at", "updated_at", "fecha_programada", "fase", "prioridad", "subfase_tecnica"]

    def get_queryset(self):
        queryset = super().get_queryset()
        role = self._role(self.request.user)
        include_bajas = self._parse_bool_query(self.request.query_params.get("include_bajas"))

        if role == "tecnico":
            queryset = queryset.filter(tecnico_asignado__user=self.request.user)

        can_include_bajas = include_bajas and role in {"coordinador", "admin"}
        if not can_include_bajas:
            queryset = queryset.exclude(status_operativo=Pedido.StatusOperativo.DADO_DE_BAJA)

        return queryset

    def create(self, request, *args, **kwargs):
        self._require_coordinador_o_admin()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self._require_coordinador_o_admin()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self._require_coordinador_o_admin()
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._require_coordinador_o_admin()
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        pedido = serializer.save()
        sync_pedido_to_mongo(pedido)

    def perform_update(self, serializer):
        instance = serializer.instance
        next_status = serializer.validated_data.get("status_operativo", instance.status_operativo)
        if (
            instance.status_operativo == Pedido.StatusOperativo.DADO_DE_BAJA
            and next_status != Pedido.StatusOperativo.DADO_DE_BAJA
        ):
            raise ValidationError({"status_operativo": "Un pedido dado de baja no puede reactivarse."})

        pedido = serializer.save()
        sync_pedido_to_mongo(pedido)

    def perform_destroy(self, instance):
        pedido_id = instance.id
        instance.delete()
        delete_pedido_from_mongo(pedido_id)

    def _role(self, user):
        tecnico = self._tecnico_perfil(user)
        if getattr(user, "is_superuser", False):
            return "admin"
        if getattr(user, "is_staff", False) or user.groups.filter(name__iexact="coordinador").exists():
            return "coordinador"
        if tecnico is not None:
            return "tecnico"
        return "usuario"

    def _tecnico_perfil(self, user):
        try:
            return user.tecnico_perfil
        except Exception:
            return None

    def _parse_bool_query(self, value):
        if value is None:
            return False
        return str(value).strip().lower() in {"1", "true", "yes", "si", "on"}

    def _require_coordinador_o_admin(self):
        if self._role(self.request.user) not in {"coordinador", "admin"}:
            raise PermissionDenied("Solo coordinadores o administradores pueden ejecutar esta accion.")

    def _require_tecnico_asignado(self, pedido: Pedido):
        tecnico = self._tecnico_perfil(self.request.user)
        if not tecnico:
            raise PermissionDenied("Debes tener un perfil tecnico asociado a tu usuario.")
        if pedido.tecnico_asignado_id != tecnico.id:
            raise PermissionDenied("Este pedido no esta asignado a tu perfil tecnico.")
        return tecnico

    def _save_pedido_con_historial(self, pedido: Pedido, evento: str, detalle: str, update_fields: list[str]):
        pedido.agregar_historial(evento=evento, usuario=self.request.user, detalle=detalle)
        merged_fields = set(update_fields)
        merged_fields.update({"historial", "updated_at"})
        pedido.save(update_fields=list(merged_fields))
        sync_pedido_to_mongo(pedido)

    @action(detail=True, methods=["post"])
    def recomendar_tecnico(self, request, pk=None):
        self._require_coordinador_o_admin()
        pedido = self.get_object()
        payload = recomendar_tecnico_para_pedido(pedido)
        return Response(payload)

    @action(detail=True, methods=["post"])
    def auto_asignar(self, request, pk=None):
        self._require_coordinador_o_admin()
        pedido = self.get_object()
        payload = recomendar_tecnico_para_pedido(pedido)
        tecnico_id = payload.get("sugerido", {}).get("id")
        if tecnico_id:
            pedido.tecnico_asignado_id = tecnico_id
            pedido.fase = Pedido.Fase.PROGRAMACION
            pedido.status_operativo = Pedido.StatusOperativo.POR_CONFIRMAR
            pedido.subfase_tecnica = Pedido.SubfaseTecnica.CONFIRMACION
            self._save_pedido_con_historial(
                pedido,
                evento="auto_asignacion",
                detalle=f"Tecnico asignado automaticamente: {tecnico_id}",
                update_fields=["tecnico_asignado", "fase", "status_operativo", "subfase_tecnica"],
            )
            payload["auto_asignado"] = True
        else:
            payload["auto_asignado"] = False
        return Response(payload)

    @action(detail=False, methods=["get"], url_path="mis-asignados")
    def mis_asignados(self, request):
        if self._role(request.user) != "tecnico":
            raise PermissionDenied("Solo los tecnicos tienen pedidos asignados en esta vista.")
        queryset = self.get_queryset().order_by("-updated_at")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="confirmar-tecnico")
    def confirmar_tecnico(self, request, pk=None):
        pedido = self.get_object()
        tecnico = self._require_tecnico_asignado(pedido)

        if pedido.fase == Pedido.Fase.CREACION:
            pedido.fase = Pedido.Fase.PROGRAMACION
        pedido.status_operativo = Pedido.StatusOperativo.CONFIRMADO
        pedido.subfase_tecnica = Pedido.SubfaseTecnica.EJECUCION
        self._save_pedido_con_historial(
            pedido,
            evento="confirmacion_tecnico",
            detalle="El tecnico confirmo la recepcion del pedido.",
            update_fields=["fase", "status_operativo", "subfase_tecnica"],
        )

        TecnicoUpdate.objects.create(
            pedido=pedido,
            tecnico=tecnico,
            nota="Pedido confirmado por tecnico.",
            nuevo_estado=Pedido.StatusOperativo.CONFIRMADO,
        )
        return Response(self.get_serializer(pedido).data)

    @action(detail=True, methods=["get", "post"], url_path="checklist")
    def checklist(self, request, pk=None):
        pedido = self.get_object()
        tecnico = self._require_tecnico_asignado(pedido)

        if request.method.lower() == "get":
            queryset = pedido.checklist_steps.select_related("tecnico").all()
            serializer = ChecklistStepSerializer(queryset, many=True)
            return Response(serializer.data)

        step_id = request.data.get("step_id")
        if step_id not in {choice[0] for choice in ChecklistStep.StepId.choices}:
            raise ValidationError({"step_id": "Paso de checklist no valido."})

        raw_completado = request.data.get("completado", True)
        if isinstance(raw_completado, str):
            completado = raw_completado.strip().lower() in {"1", "true", "yes", "si", "on"}
        else:
            completado = bool(raw_completado)

        nota = (request.data.get("nota") or "").strip()
        if step_id == ChecklistStep.StepId.NOTA_ADICIONAL and not nota:
            raise ValidationError({"nota": "La nota adicional es obligatoria para este paso."})

        step, created = ChecklistStep.objects.get_or_create(
            pedido=pedido,
            step_id=step_id,
            defaults={
                "tecnico": tecnico,
                "completado": completado,
                "nota": nota,
            },
        )
        if not created:
            step.tecnico = tecnico
            step.completado = completado
            step.nota = nota or step.nota

        step.completado_en = timezone.now() if step.completado else None
        step.save()

        if step.completado and pedido.fecha_inicio_labor is None:
            pedido.fecha_inicio_labor = timezone.now()

        required_steps = {choice[0] for choice in ChecklistStep.StepId.choices}
        completed_steps = set(
            pedido.checklist_steps.filter(completado=True).values_list("step_id", flat=True)
        )

        if required_steps.issubset(completed_steps):
            pedido.subfase_tecnica = Pedido.SubfaseTecnica.EVIDENCIAS
        else:
            pedido.subfase_tecnica = Pedido.SubfaseTecnica.EJECUCION

        pedido.status_operativo = Pedido.StatusOperativo.EN_LABOR
        if pedido.fase in {Pedido.Fase.CREACION, Pedido.Fase.PROGRAMACION}:
            pedido.fase = Pedido.Fase.SEGUIMIENTO

        self._save_pedido_con_historial(
            pedido,
            evento="checklist_tecnico",
            detalle=f"Paso actualizado: {step.step_id}",
            update_fields=["fase", "status_operativo", "subfase_tecnica", "fecha_inicio_labor"],
        )

        TecnicoUpdate.objects.create(
            pedido=pedido,
            tecnico=tecnico,
            nota=f"Checklist actualizado: {step.step_id}",
            nuevo_estado=pedido.status_operativo,
        )

        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(ChecklistStepSerializer(step).data, status=response_status)

    @action(detail=True, methods=["get", "post"], url_path="evidencias")
    def evidencias(self, request, pk=None):
        pedido = self.get_object()
        tecnico = self._require_tecnico_asignado(pedido)

        if request.method.lower() == "get":
            queryset = pedido.evidencias.select_related("tecnico").all()
            stage = request.query_params.get("stage")
            if stage:
                queryset = queryset.filter(stage=stage)
            serializer = EvidenciaSerializer(queryset, many=True, context={"request": request})
            return Response(serializer.data)

        archivo = request.FILES.get("archivo")
        descripcion = (request.data.get("descripcion") or "").strip()
        stage = request.data.get("stage")
        source = request.data.get("source", Evidencia.Source.ARCHIVO)
        nombre = (request.data.get("nombre") or "").strip()

        if not archivo:
            raise ValidationError({"archivo": "Debes adjuntar un archivo de evidencia."})
        if not descripcion:
            raise ValidationError({"descripcion": "La descripcion de la evidencia es obligatoria."})
        if stage not in {Evidencia.Stage.ANTES, Evidencia.Stage.DESPUES}:
            raise ValidationError({"stage": "Debes enviar stage=antes o stage=despues."})
        if source not in {Evidencia.Source.ARCHIVO, Evidencia.Source.CAMARA}:
            raise ValidationError({"source": "Debes enviar source=archivo o source=camara."})

        evidencia = Evidencia.objects.create(
            pedido=pedido,
            tecnico=tecnico,
            nombre=nombre or archivo.name,
            archivo=archivo,
            descripcion=descripcion,
            stage=stage,
            source=source,
        )

        has_antes = pedido.evidencias.filter(stage=Evidencia.Stage.ANTES).exists()
        has_despues = pedido.evidencias.filter(stage=Evidencia.Stage.DESPUES).exists()
        if has_antes and has_despues:
            pedido.subfase_tecnica = Pedido.SubfaseTecnica.CIERRE_TECNICO
            pedido.status_operativo = Pedido.StatusOperativo.CIERRE_TECNICO
        else:
            pedido.subfase_tecnica = Pedido.SubfaseTecnica.EVIDENCIAS
            pedido.status_operativo = Pedido.StatusOperativo.EN_LABOR

        self._save_pedido_con_historial(
            pedido,
            evento="evidencia_tecnica",
            detalle=f"Evidencia registrada ({stage}): {evidencia.nombre}",
            update_fields=["status_operativo", "subfase_tecnica"],
        )

        TecnicoUpdate.objects.create(
            pedido=pedido,
            tecnico=tecnico,
            nota=f"Evidencia enviada: {evidencia.nombre}",
            nuevo_estado=pedido.status_operativo,
        )
        return Response(EvidenciaSerializer(evidencia, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="diagnostico")
    def diagnostico(self, request, pk=None):
        pedido = self.get_object()
        role = self._role(request.user)
        if role == "tecnico":
            self._require_tecnico_asignado(pedido)
        elif role not in {"coordinador", "admin"}:
            raise PermissionDenied("No tienes permisos para actualizar el diagnostico.")

        diagnostico = (request.data.get("diagnostico_tecnico") or "").strip()
        if not diagnostico:
            raise ValidationError({"diagnostico_tecnico": "El diagnostico tecnico no puede estar vacio."})

        pedido.diagnostico_tecnico = diagnostico
        self._save_pedido_con_historial(
            pedido,
            evento="diagnostico_tecnico",
            detalle="Diagnostico tecnico actualizado.",
            update_fields=["diagnostico_tecnico"],
        )
        return Response(self.get_serializer(pedido).data)

    @action(detail=True, methods=["post"], url_path="informe-tecnico")
    def informe_tecnico(self, request, pk=None):
        pedido = self.get_object()
        tecnico = self._require_tecnico_asignado(pedido)

        diagnostico_final = (request.data.get("diagnostico_final") or "").strip()
        observaciones = (request.data.get("observaciones") or "").strip()
        recomendaciones = (request.data.get("recomendaciones") or "").strip()
        responsable_local = (request.data.get("responsable_local") or "").strip()
        pedido_solicitado = (request.data.get("pedido_solicitado") or "").strip()
        firma_cliente = request.FILES.get("firma_cliente")

        if not diagnostico_final:
            raise ValidationError({"diagnostico_final": "El diagnostico final es obligatorio."})
        if not observaciones:
            raise ValidationError({"observaciones": "Las observaciones son obligatorias."})
        if not recomendaciones:
            raise ValidationError({"recomendaciones": "Las recomendaciones son obligatorias."})

        informe = getattr(pedido, "informe_tecnico", None)
        creating = informe is None
        if creating:
            if not firma_cliente:
                raise ValidationError({"firma_cliente": "Debes adjuntar la firma del cliente."})
            informe = InformeTecnico(
                pedido=pedido,
                tecnico=tecnico,
            )

        informe.tecnico = tecnico
        informe.diagnostico_final = diagnostico_final
        informe.observaciones = observaciones
        informe.recomendaciones = recomendaciones
        informe.responsable_local = responsable_local
        informe.pedido_solicitado = pedido_solicitado
        if firma_cliente:
            informe.firma_cliente = firma_cliente
        elif creating:
            raise ValidationError({"firma_cliente": "Debes adjuntar la firma del cliente."})
        informe.save()

        now = timezone.now()
        pedido.diagnostico_tecnico = diagnostico_final
        pedido.status_operativo = Pedido.StatusOperativo.COMPLETADO
        pedido.subfase_tecnica = Pedido.SubfaseTecnica.FACTURACION
        pedido.fase = Pedido.Fase.CIERRE
        pedido.fecha_fin_labor = now
        pedido.fecha_cierre = now
        self._save_pedido_con_historial(
            pedido,
            evento="informe_tecnico",
            detalle="Informe tecnico enviado y pedido marcado como completado.",
            update_fields=[
                "diagnostico_tecnico",
                "status_operativo",
                "subfase_tecnica",
                "fase",
                "fecha_fin_labor",
                "fecha_cierre",
            ],
        )

        TecnicoUpdate.objects.create(
            pedido=pedido,
            tecnico=tecnico,
            nota="Informe tecnico enviado. Pedido completado.",
            nuevo_estado=Pedido.StatusOperativo.COMPLETADO,
        )

        return Response(
            {
                "pedido": self.get_serializer(pedido).data,
                "informe": InformeTecnicoSerializer(informe, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED if creating else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="dar-baja")
    def dar_baja(self, request, pk=None):
        self._require_coordinador_o_admin()
        pedido = self.get_object()

        if pedido.status_operativo == Pedido.StatusOperativo.DADO_DE_BAJA:
            return Response(self.get_serializer(pedido).data)

        motivo = (request.data.get("motivo") or "").strip()
        detalle = "Pedido marcado como dado de baja."
        if motivo:
            detalle = f"{detalle} Motivo: {motivo}"

        pedido.status_operativo = Pedido.StatusOperativo.DADO_DE_BAJA
        pedido.fase = Pedido.Fase.CIERRE
        if pedido.fecha_cierre is None:
            pedido.fecha_cierre = timezone.now()

        self._save_pedido_con_historial(
            pedido,
            evento="baja_operativa",
            detalle=detalle,
            update_fields=["status_operativo", "fase", "fecha_cierre"],
        )

        TecnicoUpdate.objects.create(
            pedido=pedido,
            tecnico=self._tecnico_perfil(request.user),
            nota=motivo or "Pedido dado de baja por coordinacion.",
            nuevo_estado=Pedido.StatusOperativo.DADO_DE_BAJA,
        )

        return Response(self.get_serializer(pedido).data)

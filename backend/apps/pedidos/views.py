"""Vistas de Pedidos — delgadas por diseno.

Toda logica de negocio vive en services.py.  Aqui solo:
    1. Validar permisos.
    2. Deserializar entrada.
    3. Llamar al servicio.
    4. Serializar y retornar la respuesta.
"""
from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.permissions import IsCoordinadorOrAdmin, IsTecnico
from apps.accounts.roles import tecnico_perfil

from . import services
from .models import Pedido
from .serializers import (
    ChecklistStepSerializer,
    EvidenciaSerializer,
    InformeTecnicoSerializer,
    PedidoSerializer,
)


def _validation_error_response(exc: DjangoValidationError) -> Response:
    if hasattr(exc, "message_dict"):
        return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)
    return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)


class PedidoViewSet(viewsets.ModelViewSet):
    """CRUD + acciones de workflow para Pedido."""

    queryset = (
        Pedido.objects.select_related("cliente", "cuenta", "tecnico_asignado")
        .prefetch_related(
            "checklist_steps",
            "evidencias",
            "tecnico_updates",
            "informe_tecnico",
        )
        .all()
    )
    serializer_class = PedidoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["fase", "status_operativo", "prioridad", "tecnico_asignado"]
    search_fields = ["codigo", "titulo", "descripcion", "zona", "tipo_servicio"]
    ordering_fields = ["created_at", "fecha_programada", "prioridad"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [IsAuthenticated()]
        if self.action in {"create", "update", "partial_update", "destroy", "dar_de_baja"}:
            return [IsCoordinadorOrAdmin()]
        if self.action in {
            "confirmar",
            "checklist",
            "evidencia",
            "diagnostico",
            "informe",
        }:
            return [IsTecnico()]
        return [IsAuthenticated()]

    # ------------------------------------------------------------------ #
    # CRUD overrides                                                       #
    # ------------------------------------------------------------------ #
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # El tecnico solo ve sus pedidos asignados
        tecnico = tecnico_perfil(user)
        if tecnico and not (user.is_staff or user.groups.filter(name="coordinadores").exists()):
            qs = qs.filter(tecnico_asignado=tecnico)
        return qs

    # ------------------------------------------------------------------ #
    # Acciones del coordinador                                            #
    # ------------------------------------------------------------------ #
    @action(detail=True, methods=["post"], permission_classes=[IsCoordinadorOrAdmin])
    def dar_de_baja(self, request: Request, pk=None) -> Response:
        pedido = self.get_object()
        motivo = request.data.get("motivo", "")
        services.dar_de_baja(pedido, usuario=request.user, motivo=motivo)
        return Response(PedidoSerializer(pedido).data)

    # ------------------------------------------------------------------ #
    # Acciones del tecnico                                                #
    # ------------------------------------------------------------------ #
    @action(detail=True, methods=["post"], permission_classes=[IsTecnico])
    def confirmar(self, request: Request, pk=None) -> Response:
        pedido = self.get_object()
        tecnico = tecnico_perfil(request.user)
        try:
            services.confirmar_pedido(pedido, tecnico=tecnico, usuario=request.user)
        except services.WorkflowError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(PedidoSerializer(pedido).data)

    @action(detail=True, methods=["post"], permission_classes=[IsTecnico])
    def checklist(self, request: Request, pk=None) -> Response:
        pedido = self.get_object()
        tecnico = tecnico_perfil(request.user)
        step_id = request.data.get("step_id", "")
        completado = bool(request.data.get("completado", False))
        nota = request.data.get("nota", "")
        try:
            step, _ = services.upsert_checklist_step(
                pedido,
                tecnico=tecnico,
                usuario=request.user,
                step_id=step_id,
                completado=completado,
                nota=nota,
            )
        except DjangoValidationError as exc:
            return _validation_error_response(exc)
        return Response(ChecklistStepSerializer(step).data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsTecnico],
        parser_classes=[MultiPartParser, FormParser],
    )
    def evidencia(self, request: Request, pk=None) -> Response:
        pedido = self.get_object()
        tecnico = tecnico_perfil(request.user)
        archivo = request.FILES.get("archivo")
        if not archivo:
            return Response({"archivo": "Se requiere un archivo."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            ev = services.registrar_evidencia(
                pedido,
                tecnico=tecnico,
                usuario=request.user,
                archivo=archivo,
                descripcion=request.data.get("descripcion", ""),
                stage=request.data.get("stage", ""),
                source=request.data.get("source", "archivo"),
                nombre=request.data.get("nombre", ""),
            )
        except DjangoValidationError as exc:
            return _validation_error_response(exc)
        return Response(EvidenciaSerializer(ev).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], permission_classes=[IsTecnico])
    def diagnostico(self, request: Request, pk=None) -> Response:
        pedido = self.get_object()
        try:
            services.actualizar_diagnostico(
                pedido,
                usuario=request.user,
                diagnostico=request.data.get("diagnostico_tecnico", ""),
            )
        except DjangoValidationError as exc:
            return _validation_error_response(exc)
        return Response(PedidoSerializer(pedido).data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsTecnico],
        parser_classes=[MultiPartParser, FormParser],
    )
    def informe(self, request: Request, pk=None) -> Response:
        pedido = self.get_object()
        tecnico = tecnico_perfil(request.user)
        try:
            informe, _ = services.cerrar_con_informe(
                pedido,
                tecnico=tecnico,
                usuario=request.user,
                diagnostico_final=request.data.get("diagnostico_final", ""),
                responsable_local=request.data.get("responsable_local", ""),
                pedido_solicitado=request.data.get("pedido_solicitado", ""),
                observaciones=request.data.get("observaciones", ""),
                recomendaciones=request.data.get("recomendaciones", ""),
                firma_cliente=request.FILES.get("firma_cliente"),
            )
        except DjangoValidationError as exc:
            return _validation_error_response(exc)
        return Response(InformeTecnicoSerializer(informe).data, status=status.HTTP_200_OK)

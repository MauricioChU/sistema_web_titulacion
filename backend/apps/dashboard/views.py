"""KPIs para el dashboard del coordinador.

GET /api/dashboard/kpis/ → resumen operativo.
GET /api/dashboard/pedidos-por-estado/ → conteo agrupado.
GET /api/dashboard/pedidos-por-tecnico/ → carga de trabajo actual.
"""
from __future__ import annotations

from django.db.models import Count, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.pedidos.models import Pedido
from apps.tecnicos.models import Tecnico


class KpiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        total = Pedido.objects.count()
        activos = Pedido.objects.filter(
            status_operativo__in=[
                Pedido.StatusOperativo.POR_CONFIRMAR,
                Pedido.StatusOperativo.CONFIRMADO,
                Pedido.StatusOperativo.EN_LABOR,
                Pedido.StatusOperativo.CIERRE_TECNICO,
            ]
        ).count()
        completados = Pedido.objects.filter(
            status_operativo=Pedido.StatusOperativo.COMPLETADO
        ).count()
        dados_de_baja = Pedido.objects.filter(
            status_operativo=Pedido.StatusOperativo.DADO_DE_BAJA
        ).count()
        tecnicos_activos = Tecnico.objects.filter(activo=True).count()
        sin_tecnico = Pedido.objects.filter(
            tecnico_asignado__isnull=True,
            fase__in=[Pedido.Fase.CREACION, Pedido.Fase.PROGRAMACION],
        ).count()

        return Response(
            {
                "total_pedidos": total,
                "pedidos_activos": activos,
                "pedidos_completados": completados,
                "pedidos_dados_de_baja": dados_de_baja,
                "tecnicos_activos": tecnicos_activos,
                "pedidos_sin_tecnico": sin_tecnico,
            }
        )


class PedidosPorEstadoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        qs = (
            Pedido.objects.values("status_operativo")
            .annotate(total=Count("id"))
            .order_by("status_operativo")
        )
        return Response(list(qs))


class PedidosPorTecnicoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        qs = (
            Pedido.objects.filter(
                tecnico_asignado__isnull=False,
                status_operativo__in=[
                    Pedido.StatusOperativo.POR_CONFIRMAR,
                    Pedido.StatusOperativo.CONFIRMADO,
                    Pedido.StatusOperativo.EN_LABOR,
                    Pedido.StatusOperativo.CIERRE_TECNICO,
                ],
            )
            .values("tecnico_asignado__id", "tecnico_asignado__nombre")
            .annotate(pedidos_activos=Count("id"))
            .order_by("-pedidos_activos")
        )
        return Response(
            [
                {
                    "tecnico_id": row["tecnico_asignado__id"],
                    "tecnico_nombre": row["tecnico_asignado__nombre"],
                    "pedidos_activos": row["pedidos_activos"],
                }
                for row in qs
            ]
        )

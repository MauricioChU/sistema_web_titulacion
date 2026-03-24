from django.db.models import Count
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.pedidos.models import Pedido
from apps.tecnicos.models import Tecnico


class DashboardResumenView(APIView):
    def get(self, request):
        por_fase_qs = Pedido.objects.values("fase").annotate(total=Count("id"))
        por_fase = {item["fase"]: item["total"] for item in por_fase_qs}

        hoy = timezone.localdate()
        pedidos_hoy = Pedido.objects.filter(created_at__date=hoy).count()

        payload = {
            "kpis": {
                "pedidos_totales": Pedido.objects.count(),
                "pedidos_hoy": pedidos_hoy,
                "tecnicos_activos": Tecnico.objects.filter(activo=True).count(),
                "pedidos_sin_tecnico": Pedido.objects.filter(tecnico_asignado__isnull=True).count(),
            },
            "pedidos_por_fase": {
                "creacion": por_fase.get(Pedido.Fase.CREACION, 0),
                "programacion": por_fase.get(Pedido.Fase.PROGRAMACION, 0),
                "seguimiento": por_fase.get(Pedido.Fase.SEGUIMIENTO, 0),
                "cierre": por_fase.get(Pedido.Fase.CIERRE, 0),
            },
        }
        return Response(payload)

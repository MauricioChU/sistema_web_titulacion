from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.recomendaciones.services import recomendar_tecnico_para_pedido
from .models import Pedido
from .serializers import PedidoSerializer


class PedidoViewSet(ModelViewSet):
    queryset = Pedido.objects.select_related("cliente", "cuenta", "tecnico_asignado").all()
    serializer_class = PedidoSerializer
    filterset_fields = ["fase", "prioridad", "cliente", "cuenta", "tecnico_asignado", "zona", "tipo_servicio"]
    search_fields = ["titulo", "descripcion", "cliente__nombre", "cuenta__nombre", "tecnico_asignado__nombre"]
    ordering_fields = ["created_at", "updated_at", "fecha_programada", "fase", "prioridad"]

    @action(detail=True, methods=["post"])
    def recomendar_tecnico(self, request, pk=None):
        pedido = self.get_object()
        payload = recomendar_tecnico_para_pedido(pedido)
        return Response(payload)

    @action(detail=True, methods=["post"])
    def auto_asignar(self, request, pk=None):
        pedido = self.get_object()
        payload = recomendar_tecnico_para_pedido(pedido)
        tecnico_id = payload.get("sugerido", {}).get("id")
        if tecnico_id:
            pedido.tecnico_asignado_id = tecnico_id
            pedido.fase = Pedido.Fase.PROGRAMACION
            pedido.save(update_fields=["tecnico_asignado", "fase", "updated_at"])
            payload["auto_asignado"] = True
        else:
            payload["auto_asignado"] = False
        return Response(payload)

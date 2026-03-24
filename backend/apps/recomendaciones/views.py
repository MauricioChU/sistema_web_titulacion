from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.pedidos.models import Pedido
from .services import recomendar_tecnico_para_pedido


class RecomendacionPedidoView(APIView):
    def get(self, request, pedido_id: int):
        pedido = get_object_or_404(Pedido, pk=pedido_id)
        payload = recomendar_tecnico_para_pedido(pedido)
        return Response(payload)

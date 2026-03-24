from django.urls import path
from .views import RecomendacionPedidoView

urlpatterns = [
    path(
        "recomendaciones/pedidos/<int:pedido_id>/tecnico-sugerido/",
        RecomendacionPedidoView.as_view(),
        name="recomendacion-tecnico-pedido",
    ),
]

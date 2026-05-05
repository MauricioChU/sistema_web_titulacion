from django.urls import path
from .views_new import (
    PedidoListView, PedidoDetailView,
    PedidoAsignarView, PedidoReasignarView,
    PedidoCompletarView, PedidoDarDeBajaView,
    PedidoConfirmarView, PedidoRechazarView,
    PedidoChecklistView, PedidoEvidenciaView,
    PedidoDiagnosticoView, PedidoMaterialesView,
    PedidoInformeView,
)

urlpatterns = [
    path("", PedidoListView.as_view(), name="pedido-list"),
    path("<str:pk>/", PedidoDetailView.as_view(), name="pedido-detail"),
    path("<str:pk>/asignar/", PedidoAsignarView.as_view(), name="pedido-asignar"),
    path("<str:pk>/reasignar/", PedidoReasignarView.as_view(), name="pedido-reasignar"),
    path("<str:pk>/completar/", PedidoCompletarView.as_view(), name="pedido-completar"),
    path("<str:pk>/dar-de-baja/", PedidoDarDeBajaView.as_view(), name="pedido-dar-baja"),
    path("<str:pk>/confirmar/", PedidoConfirmarView.as_view(), name="pedido-confirmar"),
    path("<str:pk>/rechazar/", PedidoRechazarView.as_view(), name="pedido-rechazar"),
    path("<str:pk>/checklist/", PedidoChecklistView.as_view(), name="pedido-checklist"),
    path("<str:pk>/evidencia/", PedidoEvidenciaView.as_view(), name="pedido-evidencia"),
    path("<str:pk>/diagnostico/", PedidoDiagnosticoView.as_view(), name="pedido-diagnostico"),
    path("<str:pk>/materiales/", PedidoMaterialesView.as_view(), name="pedido-materiales"),
    path("<str:pk>/informe/", PedidoInformeView.as_view(), name="pedido-informe"),
]

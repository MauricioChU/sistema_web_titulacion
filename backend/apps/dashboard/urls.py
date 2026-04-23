from django.urls import path

from .views import KpiView, PedidosPorEstadoView, PedidosPorTecnicoView

urlpatterns = [
    path("dashboard/kpis/", KpiView.as_view(), name="dashboard-kpis"),
    path("dashboard/pedidos-por-estado/", PedidosPorEstadoView.as_view(), name="dashboard-por-estado"),
    path("dashboard/pedidos-por-tecnico/", PedidosPorTecnicoView.as_view(), name="dashboard-por-tecnico"),
]

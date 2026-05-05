from django.urls import path
from .views import ReportePedidoView

urlpatterns = [
    path("pedido/<str:pk>/pdf/", ReportePedidoView.as_view(), name="reporte-pedido-pdf"),
]

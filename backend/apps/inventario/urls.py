from django.urls import path
from .views import InventarioListView, InventarioDetailView

urlpatterns = [
    path("", InventarioListView.as_view(), name="inventario-list"),
    path("<str:pk>/", InventarioDetailView.as_view(), name="inventario-detail"),
]

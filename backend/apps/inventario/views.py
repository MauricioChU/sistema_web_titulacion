from rest_framework.viewsets import ModelViewSet

from .models import ItemInventario
from .serializers import ItemInventarioSerializer


class ItemInventarioViewSet(ModelViewSet):
    queryset = ItemInventario.objects.all()
    serializer_class = ItemInventarioSerializer
    filterset_fields = ["categoria", "almacen", "activo"]
    search_fields = ["sku", "descripcion", "categoria", "almacen"]
    ordering_fields = ["sku", "descripcion", "stock", "updated_at"]

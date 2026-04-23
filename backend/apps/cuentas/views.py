from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import ReadAllWriteCoordinador

from .models import Cuenta
from .serializers import CuentaSerializer


class CuentaViewSet(ModelViewSet):
    queryset = Cuenta.objects.select_related("cliente").all()
    serializer_class = CuentaSerializer
    permission_classes = [ReadAllWriteCoordinador]
    filterset_fields = ["cliente", "tipo", "activa"]
    search_fields = ["nombre", "numero", "direccion", "distrito", "cliente__nombre"]
    ordering_fields = ["nombre", "created_at"]

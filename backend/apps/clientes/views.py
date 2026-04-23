from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import ReadAllWriteCoordinador

from .models import Cliente
from .serializers import ClienteSerializer


class ClienteViewSet(ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [ReadAllWriteCoordinador]
    filterset_fields = ["activo"]
    search_fields = ["nombre", "documento", "telefono", "correo"]
    ordering_fields = ["nombre", "created_at"]

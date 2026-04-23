from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import ReadAllWriteCoordinador

from .models import Tecnico
from .serializers import TecnicoSerializer


class TecnicoViewSet(ModelViewSet):
    queryset = Tecnico.objects.select_related("user").all()
    serializer_class = TecnicoSerializer
    permission_classes = [ReadAllWriteCoordinador]
    filterset_fields = ["zona", "especialidad", "activo"]
    search_fields = ["nombre", "especialidad", "zona"]
    ordering_fields = ["nombre", "capacidad_diaria", "created_at"]

from rest_framework.viewsets import ModelViewSet
from .models import Tecnico
from .serializers import TecnicoSerializer


class TecnicoViewSet(ModelViewSet):
    queryset = Tecnico.objects.all()
    serializer_class = TecnicoSerializer
    filterset_fields = ["zona", "especialidad", "activo"]
    search_fields = ["nombre", "especialidad", "zona"]
    ordering_fields = ["nombre", "capacidad_diaria", "created_at"]

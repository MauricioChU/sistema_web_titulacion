from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"status": "ok", "timestamp": timezone.now().isoformat()})


class AuthMeView(APIView):
    permission_classes = [IsAuthenticated]

    def _tecnico_perfil(self, user):
        try:
            return user.tecnico_perfil
        except Exception:
            return None

    def get(self, request):
        user = request.user
        tecnico = self._tecnico_perfil(user)

        if user.is_superuser:
            role = "admin"
        elif tecnico is not None:
            role = "tecnico"
        elif user.is_staff or user.groups.filter(name__iexact="coordinador").exists():
            role = "coordinador"
        else:
            role = "usuario"

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
                "role": role,
                "tecnico_id": getattr(tecnico, "id", None),
                "tecnico_nombre": getattr(tecnico, "nombre", None),
            }
        )

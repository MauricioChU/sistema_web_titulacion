from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import SessionUserSerializer


class AuthMeView(APIView):
    """Retorna el usuario actual en la forma que espera el front."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(SessionUserSerializer.from_user(request.user))

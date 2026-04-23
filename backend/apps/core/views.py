"""Endpoints publicos minimos (salud, version)."""
from __future__ import annotations

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Endpoint publico usado por monitoreo y por el smoke-test del front."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"status": "ok", "timestamp": timezone.now().isoformat()})

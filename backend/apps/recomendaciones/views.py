from __future__ import annotations

from dataclasses import asdict

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import recomendar_tecnicos


class RecomendarTecnicoView(APIView):
    """GET /api/recomendaciones/tecnicos/?lat=X&lon=Y&limit=5"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        def _float(key: str):
            try:
                return float(request.query_params[key])
            except (KeyError, ValueError):
                return None

        lat = _float("lat")
        lon = _float("lon")
        limit = int(request.query_params.get("limit", 5))
        results = recomendar_tecnicos(lat, lon, limit=max(1, min(limit, 20)))
        return Response([asdict(r) for r in results])

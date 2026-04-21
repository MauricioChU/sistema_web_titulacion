from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt

from apps.pedidos.models import Pedido
from apps.tecnicos.models import Tecnico


@dataclass
class ScoreTecnico:
    tecnico: Tecnico
    score: float
    distancia_km: float | None
    motivos: list[str]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Great-circle distance between two points on Earth.
    radius_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius_km * asin(sqrt(a))


def _as_float(value) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _score_por_distancia(tecnico: Tecnico, pedido: Pedido) -> ScoreTecnico:
    cuenta = pedido.cuenta
    cuenta_lat = _as_float(getattr(cuenta, "latitud", None))
    cuenta_lon = _as_float(getattr(cuenta, "longitud", None))
    tecnico_lat = _as_float(getattr(tecnico, "latitud_base", None))
    tecnico_lon = _as_float(getattr(tecnico, "longitud_base", None))

    if cuenta_lat is None or cuenta_lon is None:
        return ScoreTecnico(
            tecnico=tecnico,
            score=0.0,
            distancia_km=None,
            motivos=["cuenta_sin_coordenadas"],
        )

    if tecnico_lat is None or tecnico_lon is None:
        return ScoreTecnico(
            tecnico=tecnico,
            score=0.0,
            distancia_km=None,
            motivos=["tecnico_sin_coordenadas"],
        )

    distance_km = _haversine_km(cuenta_lat, cuenta_lon, tecnico_lat, tecnico_lon)
    score = max(0.0, 100.0 - distance_km)
    return ScoreTecnico(
        tecnico=tecnico,
        score=round(score, 2),
        distancia_km=round(distance_km, 3),
        motivos=[f"distancia_{distance_km:.2f}km"],
    )


def recomendar_tecnico_para_pedido(pedido: Pedido) -> dict:
    tecnicos = Tecnico.objects.filter(activo=True)
    ranking = sorted(
        (_score_por_distancia(t, pedido) for t in tecnicos),
        key=lambda item: (
            item.distancia_km is None,
            item.distancia_km if item.distancia_km is not None else float("inf"),
        ),
    )

    sugerido = next((item for item in ranking if item.distancia_km is not None), None)
    return {
        "pedido_id": pedido.id,
        "sugerido": (
            {
                "id": sugerido.tecnico.id,
                "nombre": sugerido.tecnico.nombre,
                "score": sugerido.score,
                "distancia_km": sugerido.distancia_km,
                "motivos": sugerido.motivos,
            }
            if sugerido
            else None
        ),
        "ranking": [
            {
                "id": item.tecnico.id,
                "nombre": item.tecnico.nombre,
                "score": item.score,
                "distancia_km": item.distancia_km,
                "motivos": item.motivos,
            }
            for item in ranking
        ],
    }

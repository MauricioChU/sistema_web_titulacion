"""Algoritmo de recomendacion de tecnicos para un pedido.

Estrategia: puntaje combinado por distancia (haversine) + carga actual de pedidos.
Retorna una lista ordenada de tecnicos con su puntaje.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


_EARTH_RADIUS_KM = 6371.0
_MAX_DISTANCE_KM = 50.0   # radio maximo de busqueda
_MAX_PEDIDOS_ACTIVOS = 10  # para normalizar la carga


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(a))


@dataclass
class TecnicoScore:
    tecnico_id: int
    nombre: str
    distancia_km: float | None
    pedidos_activos: int
    score: float   # 0-100, mayor es mejor


def recomendar_tecnicos(
    lat: float | None,
    lon: float | None,
    *,
    limit: int = 5,
) -> list[TecnicoScore]:
    """Devuelve hasta `limit` tecnicos ordenados por puntaje descendente."""
    from django.db.models import Count

    from apps.pedidos.models import Pedido
    from apps.tecnicos.models import Tecnico

    activos_qs = (
        Pedido.objects.filter(
            status_operativo__in=[
                Pedido.StatusOperativo.CONFIRMADO,
                Pedido.StatusOperativo.EN_LABOR,
                Pedido.StatusOperativo.CIERRE_TECNICO,
            ],
            tecnico_asignado__isnull=False,
        )
        .values("tecnico_asignado_id")
        .annotate(total=Count("id"))
    )
    activos_counts: dict[int, int] = {row["tecnico_asignado_id"]: row["total"] for row in activos_qs}

    tecnicos = Tecnico.objects.filter(activo=True)
    results: list[TecnicoScore] = []

    for t in tecnicos:
        distancia: float | None = None
        dist_score = 50.0  # puntaje neutro si no hay coordenadas

        if lat is not None and lon is not None and t.latitud_base and t.longitud_base:
            try:
                distancia = _haversine(lat, lon, float(t.latitud_base), float(t.longitud_base))
            except (TypeError, ValueError):
                distancia = None

        if distancia is not None:
            if distancia > _MAX_DISTANCE_KM:
                continue
            dist_score = max(0.0, 100.0 * (1 - distancia / _MAX_DISTANCE_KM))

        carga = activos_counts.get(t.id, 0)
        carga_score = max(0.0, 100.0 * (1 - carga / _MAX_PEDIDOS_ACTIVOS))

        score = 0.6 * dist_score + 0.4 * carga_score
        results.append(
            TecnicoScore(
                tecnico_id=t.id,
                nombre=t.nombre,
                distancia_km=round(distancia, 2) if distancia is not None else None,
                pedidos_activos=carga,
                score=round(score, 2),
            )
        )

    results.sort(key=lambda x: x.score, reverse=True)
    return results[:limit]

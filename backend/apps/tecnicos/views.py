from __future__ import annotations

import math
from rest_framework.views import APIView

from apps.core.db import get_db
from apps.core.helpers import (
    bad_request, not_found, ok,
    require_oid, serialize_doc, serialize_docs, to_oid,
)
from apps.core.permissions import EsCoordinadorOAdmin


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _especialidad_coincide(especialidad: str, tipo_servicio: str) -> bool:
    """Matching simple por palabras clave entre especialidad y tipo de servicio."""
    if not especialidad or not tipo_servicio:
        return False
    palabras = {w.lower() for w in especialidad.split() if len(w) > 3}
    tipo_lower = tipo_servicio.lower()
    return any(p in tipo_lower for p in palabras)


class TecnicoListView(APIView):
    permission_classes = [EsCoordinadorOAdmin]

    def get(self, request):
        db = get_db()
        filtro: dict = {}
        activo_param = request.query_params.get("activo", "true").lower()
        if activo_param != "all":
            filtro["activo"] = activo_param != "false"
        if "zona" in request.query_params:
            filtro["zona"] = request.query_params["zona"]

        tecnicos = list(db.tecnicos.find(filtro).sort("nombre", 1))
        for t in tecnicos:
            t["pedidos_activos"] = db.pedidos.count_documents({
                "tecnico_asignado_id": t["_id"],
                "estado": {"$in": ["por-confirmar", "confirmado", "en-labor"]},
            })
        return ok(serialize_docs(tecnicos))


class TecnicoDetailView(APIView):
    permission_classes = [EsCoordinadorOAdmin]

    def get(self, request, pk):
        try:
            oid = require_oid(pk)
        except ValueError as e:
            return bad_request(str(e))
        t = get_db().tecnicos.find_one({"_id": oid})
        if not t:
            return not_found("Técnico no encontrado.")
        return ok(serialize_doc(t))


class TecnicoRecomendarView(APIView):
    """
    GET /api/tecnicos/recomendar/?pedido_id=XXX

    Devuelve el ranking completo de técnicos activos con puntuación compuesta:
      - Distancia al pedido (50%)  — se obtiene automáticamente del pedido
      - Carga de trabajo    (30%)
      - Especialidad        (20%)

    Fallback: ?lat=X&lon=Y si no se provee pedido_id.
    """
    permission_classes = [EsCoordinadorOAdmin]

    def get(self, request):
        db = get_db()

        lat_job: float = 0.0
        lon_job: float = 0.0
        tipo_servicio: str = ""
        pedido_id_str = request.query_params.get("pedido_id", "")

        # Obtener ubicación del pedido desde la cuenta asociada
        if pedido_id_str:
            try:
                oid = to_oid(pedido_id_str)
                pedido = db.pedidos.find_one({"_id": oid})
                if pedido:
                    tipo_servicio = pedido.get("tipo_servicio", "")
                    if pedido.get("cuenta_id"):
                        cuenta = db.cuentas.find_one({"_id": pedido["cuenta_id"]})
                        if cuenta:
                            lat_job = float(cuenta.get("latitud") or 0)
                            lon_job = float(cuenta.get("longitud") or 0)
            except Exception:
                pass

        # Fallback a coordenadas explícitas
        if not (lat_job and lon_job):
            try:
                lat_job = float(request.query_params.get("lat", 0))
                lon_job = float(request.query_params.get("lon", 0))
            except (ValueError, TypeError):
                pass

        tecnicos = list(db.tecnicos.find({"activo": True}))
        resultados = []

        for t in tecnicos:
            lat_t = float(t.get("latitud_base") or 0)
            lon_t = float(t.get("longitud_base") or 0)
            especialidad = t.get("especialidad", "")

            # Componente distancia
            if lat_job and lon_job and lat_t and lon_t:
                dist_km = round(_haversine(lat_job, lon_job, lat_t, lon_t), 2)
                score_dist = max(0.0, 100.0 * (1.0 - dist_km / 50.0))
            else:
                dist_km = None
                score_dist = 50.0

            # Componente carga de trabajo
            activos = db.pedidos.count_documents({
                "tecnico_asignado_id": t["_id"],
                "estado": {"$in": ["por-confirmar", "confirmado", "en-labor"]},
            })
            score_carga = max(0.0, 100.0 * (1.0 - activos / 10.0))

            # Componente especialidad
            esp_match = _especialidad_coincide(especialidad, tipo_servicio)
            score_esp = 100.0 if esp_match else 0.0

            # Puntuación final ponderada
            score_total = round(score_dist * 0.5 + score_carga * 0.3 + score_esp * 0.2, 1)

            resultados.append({
                **serialize_doc(t),
                "distancia_km": dist_km,
                "pedidos_activos": activos,
                "score": score_total,
                "score_distancia": round(score_dist, 1),
                "score_carga": round(score_carga, 1),
                "score_especialidad": score_esp,
                "specialty_match": esp_match,
            })

        resultados.sort(key=lambda x: x["score"], reverse=True)

        return ok({
            "pedido_id": pedido_id_str,
            "lat_job": lat_job,
            "lon_job": lon_job,
            "sugerido": resultados[0] if resultados else None,
            "ranking": resultados,
        })

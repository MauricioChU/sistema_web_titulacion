from __future__ import annotations

from datetime import datetime, timedelta, timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.db import get_db
from apps.core.helpers import ok, serialize_docs

ESTADOS_ACTIVOS = ("por-confirmar", "confirmado", "en-labor", "cierre-tecnico")


class DashboardView(APIView):
    """GET /api/dashboard/ → datos completos del dashboard"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        db = get_db()
        now = datetime.now(timezone.utc)
        hace7dias = now - timedelta(days=7)
        hace30dias = now - timedelta(days=30)

        # --- KPIs ---
        total = db.pedidos.count_documents({})
        activos = db.pedidos.count_documents({"estado": {"$in": list(ESTADOS_ACTIVOS)}})
        completados = db.pedidos.count_documents({"estado": "completado"})
        dados_baja = db.pedidos.count_documents({"estado": "dado-de-baja"})
        rechazados = db.pedidos.count_documents({"estado": "rechazado"})
        sin_tecnico = db.pedidos.count_documents({"tecnico_asignado_id": None, "estado": {"$nin": ["completado", "dado-de-baja"]}})
        criticos = db.pedidos.count_documents({"prioridad": "critica", "estado": {"$in": list(ESTADOS_ACTIVOS)}})
        tecnicos_activos = db.tecnicos.count_documents({"activo": True})

        # Tasa de cierre últimos 7 días
        completados_7d = db.pedidos.count_documents({"estado": "completado", "fecha_cierre": {"$gte": hace7dias}})
        creados_7d = db.pedidos.count_documents({"created_at": {"$gte": hace7dias}})
        tasa_cierre = round((completados_7d / creados_7d * 100) if creados_7d > 0 else 0, 1)

        # --- Pedidos por estado ---
        pipeline_estado = [
            {"$group": {"_id": "$estado", "total": {"$sum": 1}}},
            {"$sort": {"total": -1}},
        ]
        por_estado = [{"estado": r["_id"], "total": r["total"]} for r in db.pedidos.aggregate(pipeline_estado)]

        # --- Pedidos por prioridad ---
        pipeline_prioridad = [
            {"$match": {"estado": {"$in": list(ESTADOS_ACTIVOS)}}},
            {"$group": {"_id": "$prioridad", "total": {"$sum": 1}}},
        ]
        por_prioridad = [{"prioridad": r["_id"], "total": r["total"]} for r in db.pedidos.aggregate(pipeline_prioridad)]

        # --- Carga por técnico ---
        pipeline_tecnico = [
            {"$match": {"tecnico_asignado_id": {"$ne": None}, "estado": {"$in": list(ESTADOS_ACTIVOS)}}},
            {"$group": {"_id": "$tecnico_asignado_id", "nombre": {"$first": "$tecnico_nombre"}, "pedidos_activos": {"$sum": 1}}},
            {"$sort": {"pedidos_activos": -1}},
            {"$limit": 10},
        ]
        por_tecnico = [
            {"tecnico_id": str(r["_id"]), "tecnico_nombre": r.get("nombre", ""), "pedidos_activos": r["pedidos_activos"]}
            for r in db.pedidos.aggregate(pipeline_tecnico)
        ]

        # --- Tendencia últimos 7 días ---
        tendencia = []
        for i in range(6, -1, -1):
            dia_inicio = now - timedelta(days=i)
            dia_inicio = dia_inicio.replace(hour=0, minute=0, second=0, microsecond=0)
            dia_fin = dia_inicio + timedelta(days=1)
            creados = db.pedidos.count_documents({"created_at": {"$gte": dia_inicio, "$lt": dia_fin}})
            cerrados = db.pedidos.count_documents({"fecha_cierre": {"$gte": dia_inicio, "$lt": dia_fin}})
            tendencia.append({
                "fecha": dia_inicio.strftime("%d/%m"),
                "creados": creados,
                "cerrados": cerrados,
            })

        # --- Pedidos críticos sin asignar (alerta) ---
        alertas = list(db.pedidos.find(
            {"prioridad": {"$in": ["critica", "alta"]}, "estado": {"$in": ["por-confirmar", "rechazado"]}, "tecnico_asignado_id": None},
            {"codigo": 1, "titulo": 1, "prioridad": 1, "cliente_nombre": 1, "zona": 1, "created_at": 1}
        ).sort("created_at", -1).limit(5))

        # --- Actividad reciente ---
        actividad_raw = list(db.pedidos.find(
            {}, {"codigo": 1, "titulo": 1, "historial": {"$slice": -1}, "cliente_nombre": 1}
        ).sort("updated_at", -1).limit(15))
        actividad = []
        for p in actividad_raw:
            hist = p.get("historial", [])
            if hist:
                ultimo = hist[-1]
                actividad.append({
                    "pedido_id": str(p["_id"]),
                    "codigo": p.get("codigo", ""),
                    "titulo": p.get("titulo", ""),
                    "cliente": p.get("cliente_nombre", ""),
                    "evento": ultimo.get("evento", ""),
                    "detalle": ultimo.get("detalle", ""),
                    "usuario": ultimo.get("usuario", ""),
                    "at": ultimo.get("at", "").isoformat() if hasattr(ultimo.get("at", ""), "isoformat") else str(ultimo.get("at", "")),
                })

        # --- Pedidos con ubicación para mapa ---
        pedidos_mapa = []
        pedidos_activos_raw = list(db.pedidos.find(
            {"estado": {"$in": list(ESTADOS_ACTIVOS)}, "cuenta_id": {"$ne": None}},
            {"codigo": 1, "titulo": 1, "prioridad": 1, "estado": 1, "cuenta_id": 1, "cliente_nombre": 1, "tecnico_nombre": 1}
        ).limit(50))
        cuenta_ids = [p["cuenta_id"] for p in pedidos_activos_raw if p.get("cuenta_id")]
        cuentas_map = {
            c["_id"]: c for c in db.cuentas.find({"_id": {"$in": cuenta_ids}}, {"latitud": 1, "longitud": 1, "nombre": 1, "direccion": 1})
        }
        for p in pedidos_activos_raw:
            cuenta = cuentas_map.get(p.get("cuenta_id"))
            if cuenta and cuenta.get("latitud") and cuenta.get("longitud"):
                pedidos_mapa.append({
                    "id": str(p["_id"]),
                    "codigo": p.get("codigo", ""),
                    "titulo": p.get("titulo", ""),
                    "prioridad": p.get("prioridad", ""),
                    "estado": p.get("estado", ""),
                    "cliente": p.get("cliente_nombre", ""),
                    "tecnico": p.get("tecnico_nombre", ""),
                    "lat": cuenta["latitud"],
                    "lon": cuenta["longitud"],
                    "direccion": cuenta.get("direccion", ""),
                })

        # --- Costos del período ---
        pipeline_costos = [
            {"$match": {"created_at": {"$gte": hace30dias}}},
            {"$group": {"_id": None, "total_epps": {"$sum": "$costo_epps"}, "total_materiales": {"$sum": "$costo_materiales"}, "total": {"$sum": "$costo_total"}}},
        ]
        costos_raw = list(db.pedidos.aggregate(pipeline_costos))
        costos_mes = costos_raw[0] if costos_raw else {"total_epps": 0, "total_materiales": 0, "total": 0}
        costos_mes.pop("_id", None)

        return ok({
            "kpis": {
                "total_pedidos": total,
                "pedidos_activos": activos,
                "pedidos_completados": completados,
                "pedidos_dados_baja": dados_baja,
                "pedidos_rechazados": rechazados,
                "sin_tecnico": sin_tecnico,
                "criticos_activos": criticos,
                "tecnicos_activos": tecnicos_activos,
                "tasa_cierre_7d": tasa_cierre,
            },
            "por_estado": por_estado,
            "por_prioridad": por_prioridad,
            "por_tecnico": por_tecnico,
            "tendencia_7d": tendencia,
            "alertas": serialize_docs(alertas),
            "actividad_reciente": actividad,
            "pedidos_mapa": pedidos_mapa,
            "costos_mes": costos_mes,
        })

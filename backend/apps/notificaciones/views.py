from __future__ import annotations

from datetime import datetime, timezone

from rest_framework.views import APIView

from apps.core.db import get_db
from apps.core.helpers import bad_request, no_content, not_found, ok, require_oid, serialize_docs, to_oid


class NotificacionListView(APIView):
    """GET  /api/notificaciones/       → bandeja de entrada del usuario actual"""

    def get(self, request):
        user = request.user
        db = get_db()
        user_oid = user["_id"]
        rol = user.get("rol", "")

        # Recibir las propias + las del rol del usuario
        filtro = {
            "$or": [
                {"para_user_id": user_oid},
                {"para_rol": rol},
                {"para_rol": "todos"},
            ]
        }
        solo_no_leidas = request.query_params.get("no_leidas", "false").lower() == "true"
        if solo_no_leidas:
            filtro["leida"] = False

        notifs = list(db.notificaciones.find(filtro).sort("created_at", -1).limit(100))
        return ok(serialize_docs(notifs))


class NotificacionConteoView(APIView):
    """GET /api/notificaciones/pendientes/ → count de no leídas (para polling)"""

    def get(self, request):
        user = request.user
        db = get_db()
        rol = user.get("rol", "")

        filtro = {
            "leida": False,
            "$or": [
                {"para_user_id": user["_id"]},
                {"para_rol": rol},
                {"para_rol": "todos"},
            ],
        }
        count = db.notificaciones.count_documents(filtro)

        # Detalles de pedidos pendientes de confirmación para técnicos
        pedidos_pendientes = []
        if rol == "tecnico":
            tecnico_doc = db.tecnicos.find_one({"user_id": user["_id"]})
            if tecnico_doc:
                pendientes = list(db.pedidos.find(
                    {"tecnico_asignado_id": tecnico_doc["_id"], "estado": "por-confirmar"},
                    {"codigo": 1, "titulo": 1, "prioridad": 1},
                ).limit(10))
                pedidos_pendientes = [
                    {"id": str(p["_id"]), "codigo": p["codigo"], "titulo": p["titulo"], "prioridad": p["prioridad"]}
                    for p in pendientes
                ]

        # Pedidos rechazados para coordinadores
        pedidos_rechazados = []
        if rol in ("coordinador", "admin"):
            rechazados = list(db.pedidos.find(
                {"estado": "rechazado"},
                {"codigo": 1, "titulo": 1, "tecnico_nombre": 1, "motivo_rechazo": 1},
            ).limit(10))
            pedidos_rechazados = [
                {
                    "id": str(p["_id"]),
                    "codigo": p["codigo"],
                    "titulo": p["titulo"],
                    "tecnico_nombre": p.get("tecnico_nombre", ""),
                    "motivo_rechazo": p.get("motivo_rechazo", ""),
                }
                for p in rechazados
            ]

        return ok({
            "no_leidas": count,
            "pedidos_pendientes": pedidos_pendientes,
            "pedidos_rechazados": pedidos_rechazados,
        })


class NotificacionMarcarLeidaView(APIView):
    """PATCH /api/notificaciones/{id}/leer/"""

    def patch(self, request, pk):
        try:
            oid = require_oid(pk)
        except ValueError as e:
            return bad_request(str(e))

        db = get_db()
        result = db.notificaciones.update_one(
            {"_id": oid},
            {"$set": {"leida": True, "leida_at": datetime.now(timezone.utc)}},
        )
        if result.matched_count == 0:
            return not_found()
        return ok({"detail": "Marcada como leída."})


class NotificacionMarcarTodasLeidasView(APIView):
    """POST /api/notificaciones/leer-todas/"""

    def post(self, request):
        user = request.user
        db = get_db()
        rol = user.get("rol", "")
        now = datetime.now(timezone.utc)

        db.notificaciones.update_many(
            {
                "leida": False,
                "$or": [
                    {"para_user_id": user["_id"]},
                    {"para_rol": rol},
                    {"para_rol": "todos"},
                ],
            },
            {"$set": {"leida": True, "leida_at": now}},
        )
        return ok({"detail": "Todas marcadas como leídas."})

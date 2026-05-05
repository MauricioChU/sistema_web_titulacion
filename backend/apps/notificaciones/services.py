from __future__ import annotations

from datetime import datetime, timezone
from bson import ObjectId
from pymongo.database import Database


def crear_notificacion(
    db: Database,
    tipo: str,
    titulo: str,
    mensaje: str,
    para_rol: str | None = None,
    para_user_id: ObjectId | None = None,
    pedido_id: ObjectId | None = None,
) -> None:
    db.notificaciones.insert_one({
        "tipo": tipo,
        "titulo": titulo,
        "mensaje": mensaje,
        "para_rol": para_rol,
        "para_user_id": para_user_id,
        "pedido_id": pedido_id,
        "leida": False,
        "created_at": datetime.now(timezone.utc),
    })

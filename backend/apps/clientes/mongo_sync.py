import logging
from datetime import datetime, timezone

from apps.core.mongo import get_mongo_collection

from .models import Cliente

logger = logging.getLogger(__name__)


def _iso(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_document(cliente: Cliente):
    return {
        "_id": cliente.id,
        "cliente_id": cliente.id,
        "nombre": cliente.nombre,
        "documento": cliente.documento,
        "telefono": cliente.telefono,
        "correo": cliente.correo,
        "direccion": cliente.direccion,
        "activo": cliente.activo,
        "created_at": _iso(cliente.created_at),
        "updated_at": _iso(cliente.updated_at),
        "synced_at": _utc_now_iso(),
    }


def sync_cliente_to_mongo(cliente: Cliente):
    collection = get_mongo_collection("MONGODB_CLIENTES_COLLECTION", "clientes")
    if collection is None:
        return

    try:
        doc = _build_document(cliente)
        collection.update_one({"_id": cliente.id}, {"$set": doc}, upsert=True)
    except Exception:
        logger.exception("No se pudo sincronizar cliente %s en MongoDB.", cliente.id)


def delete_cliente_from_mongo(cliente_id: int):
    collection = get_mongo_collection("MONGODB_CLIENTES_COLLECTION", "clientes")
    if collection is None:
        return

    try:
        collection.delete_one({"_id": cliente_id})
    except Exception:
        logger.exception("No se pudo eliminar cliente %s en MongoDB.", cliente_id)

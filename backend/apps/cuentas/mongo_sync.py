import logging
from datetime import datetime, timezone

from apps.core.mongo import get_mongo_collection

from .models import Cuenta

logger = logging.getLogger(__name__)


def _iso(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def cuenta_to_mongo_doc(cuenta: Cuenta) -> dict:
    return {
        "_id": cuenta.id,
        "cuenta_id": cuenta.id,
        "cliente_id": cuenta.cliente_id,
        "cliente_nombre": getattr(cuenta.cliente, "nombre", "") if cuenta.cliente_id else "",
        "nombre": cuenta.nombre,
        "numero": cuenta.numero,
        "direccion": cuenta.direccion,
        "distrito": cuenta.distrito,
        "contacto": cuenta.contacto,
        "telefono": cuenta.telefono,
        "tipo": cuenta.tipo,
        "latitud": cuenta.latitud,
        "longitud": cuenta.longitud,
        "activa": cuenta.activa,
        "created_at": _iso(cuenta.created_at),
        "updated_at": _iso(cuenta.updated_at),
        "synced_at": _utc_now_iso(),
    }


def sync_cuenta_to_mongo(cuenta: Cuenta) -> bool:
    collection = get_mongo_collection("MONGODB_CUENTAS_COLLECTION", "cuentas")
    if collection is None:
        return False

    try:
        document = cuenta_to_mongo_doc(cuenta)
        collection.update_one({"_id": cuenta.id}, {"$set": document}, upsert=True)
        return True
    except Exception:
        logger.exception("No se pudo sincronizar cuenta %s en MongoDB.", cuenta.id)
        return False


def delete_cuenta_from_mongo(cuenta_id: int) -> bool:
    collection = get_mongo_collection("MONGODB_CUENTAS_COLLECTION", "cuentas")
    if collection is None:
        return False

    try:
        collection.delete_one({"_id": cuenta_id})
        return True
    except Exception:
        logger.exception("No se pudo eliminar cuenta %s en MongoDB.", cuenta_id)
        return False

import logging
from datetime import datetime, timezone

from apps.core.mongo import get_mongo_collection

from .models import Tecnico

logger = logging.getLogger(__name__)


def _iso(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def tecnico_to_mongo_doc(tecnico: Tecnico) -> dict:
    return {
        "_id": tecnico.id,
        "tecnico_id": tecnico.id,
        "user_id": tecnico.user_id,
        "nombre": tecnico.nombre,
        "especialidad": tecnico.especialidad,
        "zona": tecnico.zona,
        "latitud_base": tecnico.latitud_base,
        "longitud_base": tecnico.longitud_base,
        "capacidad_diaria": tecnico.capacidad_diaria,
        "activo": tecnico.activo,
        "created_at": _iso(tecnico.created_at),
        "updated_at": _iso(tecnico.updated_at),
        "synced_at": _utc_now_iso(),
    }


def sync_tecnico_to_mongo(tecnico: Tecnico) -> bool:
    collection = get_mongo_collection("MONGODB_TECNICOS_COLLECTION", "tecnicos")
    if collection is None:
        return False

    try:
        document = tecnico_to_mongo_doc(tecnico)
        collection.update_one({"_id": tecnico.id}, {"$set": document}, upsert=True)
        return True
    except Exception:
        logger.exception("No se pudo sincronizar tecnico %s en MongoDB.", tecnico.id)
        return False


def delete_tecnico_from_mongo(tecnico_id: int) -> bool:
    collection = get_mongo_collection("MONGODB_TECNICOS_COLLECTION", "tecnicos")
    if collection is None:
        return False

    try:
        collection.delete_one({"_id": tecnico_id})
        return True
    except Exception:
        logger.exception("No se pudo eliminar tecnico %s en MongoDB.", tecnico_id)
        return False

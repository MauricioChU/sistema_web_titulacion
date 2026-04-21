import logging
from datetime import datetime, timezone

from apps.core.mongo import get_mongo_collection

from .models import ItemInventario

logger = logging.getLogger(__name__)


def _iso(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def item_inventario_to_mongo_doc(item: ItemInventario) -> dict:
    return {
        "_id": item.id,
        "item_id": item.id,
        "sku": item.sku,
        "descripcion": item.descripcion,
        "categoria": item.categoria,
        "stock": item.stock,
        "stock_minimo": item.stock_minimo,
        "unidad_medida": item.unidad_medida,
        "almacen": item.almacen,
        "activo": item.activo,
        "created_at": _iso(item.created_at),
        "updated_at": _iso(item.updated_at),
        "synced_at": _utc_now_iso(),
    }


def sync_item_inventario_to_mongo(item: ItemInventario) -> bool:
    collection = get_mongo_collection("MONGODB_INVENTARIO_COLLECTION", "inventario")
    if collection is None:
        return False

    try:
        document = item_inventario_to_mongo_doc(item)
        collection.update_one({"_id": item.id}, {"$set": document}, upsert=True)
        return True
    except Exception:
        logger.exception("No se pudo sincronizar item de inventario %s en MongoDB.", item.id)
        return False


def delete_item_inventario_from_mongo(item_id: int) -> bool:
    collection = get_mongo_collection("MONGODB_INVENTARIO_COLLECTION", "inventario")
    if collection is None:
        return False

    try:
        collection.delete_one({"_id": item_id})
        return True
    except Exception:
        logger.exception("No se pudo eliminar item de inventario %s en MongoDB.", item_id)
        return False

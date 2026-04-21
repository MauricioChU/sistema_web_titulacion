import logging
from datetime import datetime, timezone

from apps.core.mongo import get_mongo_collection

from .models import Pedido

logger = logging.getLogger(__name__)


def _iso(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_document(pedido: Pedido):
    return {
        "_id": pedido.id,
        "pedido_id": pedido.id,
        "codigo": pedido.codigo,
        "cliente_id": pedido.cliente_id,
        "cliente_nombre": getattr(pedido.cliente, "nombre", "") if pedido.cliente_id else "",
        "cuenta_id": pedido.cuenta_id,
        "cuenta_nombre": getattr(pedido.cuenta, "nombre", "") if pedido.cuenta_id else "",
        "cuenta_numero": getattr(pedido.cuenta, "numero", "") if pedido.cuenta_id else "",
        "cuenta_latitud": getattr(pedido.cuenta, "latitud", None) if pedido.cuenta_id else None,
        "cuenta_longitud": getattr(pedido.cuenta, "longitud", None) if pedido.cuenta_id else None,
        "tecnico_asignado_id": pedido.tecnico_asignado_id,
        "tecnico_nombre": getattr(pedido.tecnico_asignado, "nombre", "") if pedido.tecnico_asignado_id else "",
        "titulo": pedido.titulo,
        "descripcion": pedido.descripcion,
        "tipo_servicio": pedido.tipo_servicio,
        "zona": pedido.zona,
        "prioridad": pedido.prioridad,
        "fase": pedido.fase,
        "status_operativo": pedido.status_operativo,
        "subfase_tecnica": pedido.subfase_tecnica,
        "diagnostico_tecnico": pedido.diagnostico_tecnico,
        "historial": pedido.historial or [],
        "fecha_programada": _iso(pedido.fecha_programada),
        "fecha_inicio_labor": _iso(pedido.fecha_inicio_labor),
        "fecha_fin_labor": _iso(pedido.fecha_fin_labor),
        "fecha_cierre": _iso(pedido.fecha_cierre),
        "created_at": _iso(pedido.created_at),
        "updated_at": _iso(pedido.updated_at),
        "synced_at": _utc_now_iso(),
    }


def _get_collection():
    return get_mongo_collection("MONGODB_PEDIDOS_COLLECTION", "pedidos")


def sync_pedido_to_mongo(pedido: Pedido):
    collection = _get_collection()
    if collection is None:
        return

    try:
        doc = _build_document(pedido)
        collection.update_one({"_id": pedido.id}, {"$set": doc}, upsert=True)
    except Exception:
        logger.exception("No se pudo sincronizar pedido %s en MongoDB.", pedido.id)


def delete_pedido_from_mongo(pedido_id: int):
    collection = _get_collection()
    if collection is None:
        return

    try:
        collection.delete_one({"_id": pedido_id})
    except Exception:
        logger.exception("No se pudo eliminar pedido %s en MongoDB.", pedido_id)

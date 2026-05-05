from __future__ import annotations

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from django.conf import settings

_client: MongoClient | None = None
_db: Database | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=settings.MONGODB_TIMEOUT_MS,
        )
    return _client


def get_db() -> Database:
    global _db
    if _db is None:
        _db = get_client()[settings.MONGODB_DB_NAME]
    return _db


def init_indexes() -> None:
    db = get_db()

    db.users.create_index([("username", ASCENDING)], unique=True)
    db.users.create_index([("email", ASCENDING)])

    db.tokens.create_index([("token", ASCENDING)], unique=True)
    db.tokens.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)

    db.clientes.create_index([("nombre", ASCENDING)])
    db.clientes.create_index([("ruc", ASCENDING)], unique=True, sparse=True)

    db.cuentas.create_index([("cliente_id", ASCENDING)])
    db.cuentas.create_index([("cliente_id", ASCENDING), ("numero", ASCENDING)], unique=True)

    db.tecnicos.create_index([("user_id", ASCENDING)], unique=True)
    db.tecnicos.create_index([("activo", ASCENDING)])

    db.inventario.create_index([("sku", ASCENDING)], unique=True)
    db.inventario.create_index([("categoria", ASCENDING)])

    db.pedidos.create_index([("codigo", ASCENDING)], unique=True)
    db.pedidos.create_index([("fase", ASCENDING), ("estado", ASCENDING)])
    db.pedidos.create_index([("tecnico_asignado_id", ASCENDING)])
    db.pedidos.create_index([("cliente_id", ASCENDING)])
    db.pedidos.create_index([("created_at", DESCENDING)])

    db.notificaciones.create_index([("para_user_id", ASCENDING), ("leida", ASCENDING)])
    db.notificaciones.create_index([("para_rol", ASCENDING), ("leida", ASCENDING)])
    db.notificaciones.create_index([("created_at", DESCENDING)])

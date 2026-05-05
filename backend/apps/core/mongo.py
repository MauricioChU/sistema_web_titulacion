from __future__ import annotations

from typing import Optional

from django.conf import settings
from pymongo import MongoClient
from pymongo.errors import PyMongoError


mongo_client: Optional[MongoClient] = None
mongo_database = None
mongo_connected = False


def _mask_mongo_uri(uri: str) -> str:
    if "@" not in uri:
        return uri
    prefix, suffix = uri.split("@", 1)
    if "://" in prefix:
        scheme, _ = prefix.split("://", 1)
        return f"{scheme}://***:***@{suffix}"
    return uri


def connect_mongodb() -> bool:
    global mongo_client, mongo_database, mongo_connected

    if not getattr(settings, "MONGODB_URI", "").strip() or not getattr(settings, "MONGODB_DB_NAME", "").strip():
        print("MongoDB no configurado: omitiendo conexion.")
        mongo_client = None
        mongo_database = None
        mongo_connected = False
        return False

    try:
        client = MongoClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=settings.MONGODB_SERVER_SELECTION_TIMEOUT_MS,
        )
        client.admin.command("ping")
        mongo_client = client
        mongo_database = client[settings.MONGODB_DB_NAME]
        mongo_connected = True
        print(
            f"MongoDB conectado correctamente a {_mask_mongo_uri(settings.MONGODB_URI)} "
            f"(base: {settings.MONGODB_DB_NAME})"
        )
        return True
    except PyMongoError as exc:
        mongo_client = None
        mongo_database = None
        mongo_connected = False
        print(
            f"No se pudo conectar a MongoDB en {_mask_mongo_uri(settings.MONGODB_URI)}: {exc}"
        )
        return False

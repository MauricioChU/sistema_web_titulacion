import logging
import os

logger = logging.getLogger(__name__)

_mongo_client = None
_mongo_db = None
_mongo_db_name = None


def _mongo_enabled() -> bool:
    return os.getenv("MONGODB_SYNC_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}


def _get_timeout_ms() -> int:
    raw = os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "3000")
    try:
        return int(raw)
    except ValueError:
        return 3000


def _get_db():
    global _mongo_client, _mongo_db, _mongo_db_name

    if not _mongo_enabled():
        return None

    mongo_uri = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017").strip()
    mongo_db_name = os.getenv("MONGODB_DB_NAME", "sistema_titulacion").strip()

    if not mongo_uri or not mongo_db_name:
        return None

    if _mongo_db is not None and _mongo_db_name == mongo_db_name:
        return _mongo_db

    try:
        from pymongo import MongoClient

        _mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=_get_timeout_ms())
        _mongo_db = _mongo_client[mongo_db_name]
        _mongo_db_name = mongo_db_name
        return _mongo_db
    except Exception:
        logger.exception("No se pudo inicializar conexion MongoDB.")
        return None


def get_mongo_collection(collection_env_key: str, default_collection_name: str):
    db = _get_db()
    if db is None:
        return None

    collection_name = os.getenv(collection_env_key, default_collection_name).strip() or default_collection_name
    return db[collection_name]

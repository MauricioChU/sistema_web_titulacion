import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from pymongo import MongoClient  # noqa: E402

from apps.clientes.models import Cliente  # noqa: E402
from apps.cuentas.models import Cuenta  # noqa: E402
from apps.tecnicos.models import Tecnico  # noqa: E402


def build_mongo_client():
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017").strip()
    timeout_ms = int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "3000"))
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=timeout_ms)
    client.admin.command("ping")
    return client


def collection_names():
    return {
        "db": os.getenv("MONGODB_DB_NAME", "sistema_titulacion").strip(),
        "clientes": os.getenv("MONGODB_CLIENTES_COLLECTION", "clientes").strip(),
        "cuentas": os.getenv("MONGODB_CUENTAS_COLLECTION", "cuentas").strip(),
        "tecnicos": os.getenv("MONGODB_TECNICOS_COLLECTION", "tecnicos").strip(),
    }


def must_find(collection, _id, label):
    doc = collection.find_one({"_id": _id})
    if doc is None:
        raise AssertionError(f"No se encontro documento en Mongo para {label} con _id={_id}")
    return doc


def must_not_find(collection, _id, label):
    doc = collection.find_one({"_id": _id})
    if doc is not None:
        raise AssertionError(f"El documento en Mongo para {label} con _id={_id} debio eliminarse")


def run_verification():
    tag = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    cliente = None
    cuenta = None
    tecnico = None

    mongo_client = build_mongo_client()
    names = collection_names()
    mongo_db = mongo_client[names["db"]]
    col_clientes = mongo_db[names["clientes"]]
    col_cuentas = mongo_db[names["cuentas"]]
    col_tecnicos = mongo_db[names["tecnicos"]]

    try:
        cliente = Cliente.objects.create(
            nombre=f"Cliente Sync {tag}",
            documento=f"DOC-{tag}",
            telefono="999999999",
            correo=f"cliente-sync-{tag}@example.com",
            direccion="Av Sync 100",
            activo=True,
        )
        cuenta = Cuenta.objects.create(
            cliente=cliente,
            nombre=f"Cuenta Sync {tag}",
            numero=f"CTA-{tag}",
            tipo=Cuenta.TipoCuenta.EMPRESA,
            latitud=-12.1405,
            longitud=-76.9910,
            activa=True,
        )
        tecnico = Tecnico.objects.create(
            nombre=f"Tecnico Sync {tag}",
            especialidad="Fibra Optica",
            zona="Lima",
            latitud_base=-12.0464,
            longitud_base=-77.0428,
            capacidad_diaria=4,
            activo=True,
        )

        cliente_doc = must_find(col_clientes, cliente.id, "cliente")
        cuenta_doc = must_find(col_cuentas, cuenta.id, "cuenta")
        tecnico_doc = must_find(col_tecnicos, tecnico.id, "tecnico")

        cliente.telefono = "111222333"
        cliente.save(update_fields=["telefono", "updated_at"])
        cuenta.activa = False
        cuenta.save(update_fields=["activa", "updated_at"])
        tecnico.capacidad_diaria = 7
        tecnico.save(update_fields=["capacidad_diaria", "updated_at"])

        cliente_doc_updated = must_find(col_clientes, cliente.id, "cliente")
        cuenta_doc_updated = must_find(col_cuentas, cuenta.id, "cuenta")
        tecnico_doc_updated = must_find(col_tecnicos, tecnico.id, "tecnico")

        if cliente_doc_updated.get("telefono") != "111222333":
            raise AssertionError("Cliente no se actualizo en Mongo (telefono)")
        if cuenta_doc_updated.get("activa") is not False:
            raise AssertionError("Cuenta no se actualizo en Mongo (activa)")
        if tecnico_doc_updated.get("capacidad_diaria") != 7:
            raise AssertionError("Tecnico no se actualizo en Mongo (capacidad_diaria)")
        if cuenta_doc_updated.get("latitud") is None or cuenta_doc_updated.get("longitud") is None:
            raise AssertionError("Cuenta no sincronizo coordenadas en Mongo")
        if tecnico_doc_updated.get("latitud_base") is None or tecnico_doc_updated.get("longitud_base") is None:
            raise AssertionError("Tecnico no sincronizo coordenadas base en Mongo")

        cliente_id = cliente.id
        cuenta_id = cuenta.id
        tecnico_id = tecnico.id

        cuenta.delete()
        tecnico.delete()
        cliente.delete()

        must_not_find(col_cuentas, cuenta_id, "cuenta")
        must_not_find(col_tecnicos, tecnico_id, "tecnico")
        must_not_find(col_clientes, cliente_id, "cliente")

        return {
            "ok": True,
            "mongo_db": names["db"],
            "collections": {
                "clientes": names["clientes"],
                "cuentas": names["cuentas"],
                "tecnicos": names["tecnicos"],
            },
            "created_docs": {
                "cliente": {
                    "_id": cliente_doc.get("_id"),
                    "nombre": cliente_doc.get("nombre"),
                },
                "cuenta": {
                    "_id": cuenta_doc.get("_id"),
                    "numero": cuenta_doc.get("numero"),
                },
                "tecnico": {
                    "_id": tecnico_doc.get("_id"),
                    "nombre": tecnico_doc.get("nombre"),
                },
            },
            "updated_checks": {
                "cliente_telefono": cliente_doc_updated.get("telefono"),
                "cuenta_activa": cuenta_doc_updated.get("activa"),
                "cuenta_latitud": cuenta_doc_updated.get("latitud"),
                "cuenta_longitud": cuenta_doc_updated.get("longitud"),
                "tecnico_capacidad_diaria": tecnico_doc_updated.get("capacidad_diaria"),
                "tecnico_latitud_base": tecnico_doc_updated.get("latitud_base"),
                "tecnico_longitud_base": tecnico_doc_updated.get("longitud_base"),
            },
            "delete_checks": "ok",
        }
    finally:
        mongo_client.close()


if __name__ == "__main__":
    try:
        result = run_verification()
        print(json.dumps(result, ensure_ascii=True, indent=2, default=str))
        sys.exit(0)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=True, indent=2))
        sys.exit(1)

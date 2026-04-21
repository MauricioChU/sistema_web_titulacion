import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.contrib.auth.models import Group  # noqa: E402
from pymongo import MongoClient  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402

from apps.clientes.models import Cliente  # noqa: E402
from apps.cuentas.models import Cuenta  # noqa: E402


User = get_user_model()


def to_mongo_id(value):
    text = str(value)
    if ObjectId.is_valid(text):
        return ObjectId(text)
    return value


def assert_status(response, expected_status, context):
    if response.status_code != expected_status:
        detail = getattr(response, "data", response.content.decode("utf-8", errors="ignore"))
        raise AssertionError(
            f"{context}: expected {expected_status}, got {response.status_code}. Detail: {detail}"
        )


def login_and_get_token(username, password):
    client = APIClient()
    response = client.post(
        "/api/auth/login/",
        {"username": username, "password": password},
        format="json",
    )
    assert_status(response, 200, f"Login user {username}")

    token = response.data.get("access")
    if not token:
        raise AssertionError("Login did not return access token")
    return token


def build_mongo_client():
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017").strip()
    timeout_ms = int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "3000"))
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=timeout_ms)
    client.admin.command("ping")
    return client


def run_verification():
    now_tag = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    username = "coord_script_test"
    password = "Coord12345!"

    User.objects.filter(username=username).delete()
    user = User.objects.create_user(
        username=username,
        password=password,
        email=f"{username}@example.com",
    )
    coordinador_group, _ = Group.objects.get_or_create(name="coordinador")
    user.groups.add(coordinador_group)

    cliente = Cliente.objects.create(
        nombre=f"Cliente Script {now_tag}",
        documento=f"DOC-{now_tag}",
        telefono="999999999",
        correo=f"cliente-{now_tag}@example.com",
        direccion="Av Script 123",
        activo=True,
    )

    cuenta = Cuenta.objects.create(
        cliente=cliente,
        nombre="Cuenta Principal Script",
        numero=f"CTA-{now_tag}",
        tipo=Cuenta.TipoCuenta.EMPRESA,
        latitud=-12.1211,
        longitud=-77.0297,
        activa=True,
    )

    token = login_and_get_token(username, password)
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    payload = {
        "cliente": str(cliente.id),
        "cuenta": str(cuenta.id),
        "titulo": f"Pedido Script {now_tag}",
        "descripcion": "Validacion automatica create pedido",
        "tipo_servicio": "mantenimiento electrico",
        "zona": "Miraflores",
        "prioridad": "media",
    }

    create_resp = api.post("/api/pedidos/", payload, format="json")
    assert_status(create_resp, 201, "POST /api/pedidos")
    pedido_id = create_resp.data["id"]

    detail_resp = api.get(f"/api/pedidos/{pedido_id}/")
    assert_status(detail_resp, 200, "GET /api/pedidos/{id}")

    pedido_codigo = str(detail_resp.data.get("codigo") or "")
    if not re.match(r"^A\d{4,}$", pedido_codigo):
        raise AssertionError(f"Codigo de pedido invalido: {pedido_codigo}")

    mongo_db_name = os.getenv("MONGODB_DB_NAME", "sistema_titulacion").strip()
    mongo_collection = os.getenv("MONGODB_PEDIDOS_COLLECTION", "pedidos").strip()
    mongo_client = build_mongo_client()

    try:
        doc = mongo_client[mongo_db_name][mongo_collection].find_one(
            {"_id": to_mongo_id(pedido_id)},
            {
                "_id": 1,
                "pedido_id": 1,
                "codigo": 1,
                "titulo": 1,
                "fase": 1,
                "status_operativo": 1,
                "synced_at": 1,
            },
        )
    finally:
        mongo_client.close()

    if doc is None:
        raise AssertionError(
            f"Mongo sync missing for pedido_id={pedido_id} in {mongo_db_name}.{mongo_collection}"
        )

    result = {
        "ok": True,
        "pedido_id": pedido_id,
        "pedido_codigo": pedido_codigo,
        "api_titulo": detail_resp.data.get("titulo"),
        "api_fase": detail_resp.data.get("fase"),
        "api_status_operativo": detail_resp.data.get("status_operativo"),
        "mongo_found": True,
        "mongo_db": mongo_db_name,
        "mongo_collection": mongo_collection,
        "mongo_doc": doc,
    }
    return result


if __name__ == "__main__":
    try:
        output = run_verification()
        print(json.dumps(output, ensure_ascii=True, indent=2, default=str))
        sys.exit(0)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=True, indent=2))
        sys.exit(1)

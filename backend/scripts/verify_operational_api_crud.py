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

from django.contrib.auth import get_user_model  # noqa: E402
from django.contrib.auth.models import Group  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402

from apps.clientes.models import Cliente  # noqa: E402
from apps.cuentas.models import Cuenta  # noqa: E402
from apps.inventario.models import ItemInventario  # noqa: E402
from apps.tecnicos.models import Tecnico  # noqa: E402


User = get_user_model()


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


def run_verification():
    now_tag = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    username = f"coord_api_crud_{now_tag[-8:]}"
    password = "Coord12345!"

    created_ids = {
        "cliente": None,
        "cuenta": None,
        "inventario": None,
        "tecnico": None,
        "user": None,
    }

    try:
        user = User.objects.create_user(
            username=username,
            password=password,
            email=f"{username}@example.com",
            is_staff=True,
        )
        created_ids["user"] = user.id

        coordinador_group, _ = Group.objects.get_or_create(name="coordinador")
        user.groups.add(coordinador_group)

        token = login_and_get_token(username, password)
        api = APIClient()
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        cliente_create_payload = {
            "nombre": f"Cliente CRUD {now_tag}",
            "documento": f"DOC-{now_tag}",
            "telefono": "900111222",
            "correo": f"crud-{now_tag}@example.com",
            "direccion": "Av CRUD 100",
            "activo": True,
        }
        cliente_create_resp = api.post("/api/clientes/", cliente_create_payload, format="json")
        assert_status(cliente_create_resp, 201, "POST /api/clientes")
        cliente_id = cliente_create_resp.data["id"]
        created_ids["cliente"] = cliente_id

        cliente_update_payload = {
            "telefono": "900333444",
            "direccion": "Av CRUD 999",
            "activo": False,
        }
        cliente_update_resp = api.patch(
            f"/api/clientes/{cliente_id}/",
            cliente_update_payload,
            format="json",
        )
        assert_status(cliente_update_resp, 200, "PATCH /api/clientes/{id}")

        cliente_obj = Cliente.objects.get(id=cliente_id)
        if cliente_obj.telefono != "900333444" or cliente_obj.direccion != "Av CRUD 999" or cliente_obj.activo:
            raise AssertionError("Cliente update validation failed")

        cuenta_create_payload = {
            "cliente": cliente_id,
            "nombre": "Cuenta CRUD Principal",
            "numero": f"CUE-{now_tag}",
            "direccion": "Calle Cuenta 10",
            "distrito": "Miraflores",
            "contacto": "Mesa ayuda",
            "telefono": "955111000",
            "tipo": Cuenta.TipoCuenta.EMPRESA,
            "latitud": -12.0464,
            "longitud": -77.0428,
            "activa": True,
        }
        cuenta_create_resp = api.post("/api/cuentas/", cuenta_create_payload, format="json")
        assert_status(cuenta_create_resp, 201, "POST /api/cuentas")
        cuenta_id = cuenta_create_resp.data["id"]
        created_ids["cuenta"] = cuenta_id

        cuenta_update_payload = {
            "direccion": "Calle Cuenta 20",
            "distrito": "San Isidro",
            "contacto": "Supervisor zona",
            "telefono": "955222333",
            "activa": False,
        }
        cuenta_update_resp = api.patch(
            f"/api/cuentas/{cuenta_id}/",
            cuenta_update_payload,
            format="json",
        )
        assert_status(cuenta_update_resp, 200, "PATCH /api/cuentas/{id}")

        cuenta_obj = Cuenta.objects.get(id=cuenta_id)
        if (
            cuenta_obj.direccion != "Calle Cuenta 20"
            or cuenta_obj.distrito != "San Isidro"
            or cuenta_obj.telefono != "955222333"
            or cuenta_obj.activa
        ):
            raise AssertionError("Cuenta update validation failed")

        inventario_create_payload = {
            "sku": f"SKU-CRUD-{now_tag}",
            "descripcion": "Item inventario CRUD",
            "categoria": "material",
            "stock": 4,
            "stock_minimo": 1,
            "unidad_medida": "unidad",
            "almacen": "principal",
            "activo": True,
        }
        inventario_create_resp = api.post("/api/inventario/", inventario_create_payload, format="json")
        assert_status(inventario_create_resp, 201, "POST /api/inventario")
        inventario_id = inventario_create_resp.data["id"]
        created_ids["inventario"] = inventario_id

        inventario_update_payload = {
            "stock": 9,
            "almacen": "norte",
        }
        inventario_update_resp = api.patch(
            f"/api/inventario/{inventario_id}/",
            inventario_update_payload,
            format="json",
        )
        assert_status(inventario_update_resp, 200, "PATCH /api/inventario/{id}")

        inventario_obj = ItemInventario.objects.get(id=inventario_id)
        if inventario_obj.stock != 9 or inventario_obj.almacen != "norte":
            raise AssertionError("Inventario update validation failed")

        tecnico_create_payload = {
            "nombre": f"Tecnico CRUD {now_tag}",
            "especialidad": "electrico",
            "zona": "Lima",
            "latitud_base": -12.1211,
            "longitud_base": -77.0297,
            "capacidad_diaria": 4,
            "activo": True,
        }
        tecnico_create_resp = api.post("/api/tecnicos/", tecnico_create_payload, format="json")
        assert_status(tecnico_create_resp, 201, "POST /api/tecnicos")
        tecnico_id = tecnico_create_resp.data["id"]
        created_ids["tecnico"] = tecnico_id

        tecnico_update_payload = {
            "zona": "San Isidro",
            "capacidad_diaria": 7,
            "activo": False,
        }
        tecnico_update_resp = api.patch(
            f"/api/tecnicos/{tecnico_id}/",
            tecnico_update_payload,
            format="json",
        )
        assert_status(tecnico_update_resp, 200, "PATCH /api/tecnicos/{id}")

        tecnico_obj = Tecnico.objects.get(id=tecnico_id)
        if tecnico_obj.zona != "San Isidro" or tecnico_obj.capacidad_diaria != 7 or tecnico_obj.activo:
            raise AssertionError("Tecnico update validation failed")

        delete_cuenta_resp = api.delete(f"/api/cuentas/{cuenta_id}/")
        assert_status(delete_cuenta_resp, 204, "DELETE /api/cuentas/{id}")
        created_ids["cuenta"] = None
        if Cuenta.objects.filter(id=cuenta_id).exists():
            raise AssertionError("Cuenta delete validation failed")

        delete_cliente_resp = api.delete(f"/api/clientes/{cliente_id}/")
        assert_status(delete_cliente_resp, 204, "DELETE /api/clientes/{id}")
        created_ids["cliente"] = None
        if Cliente.objects.filter(id=cliente_id).exists():
            raise AssertionError("Cliente delete validation failed")

        delete_inventario_resp = api.delete(f"/api/inventario/{inventario_id}/")
        assert_status(delete_inventario_resp, 204, "DELETE /api/inventario/{id}")
        created_ids["inventario"] = None
        if ItemInventario.objects.filter(id=inventario_id).exists():
            raise AssertionError("Inventario delete validation failed")

        delete_tecnico_resp = api.delete(f"/api/tecnicos/{tecnico_id}/")
        assert_status(delete_tecnico_resp, 204, "DELETE /api/tecnicos/{id}")
        created_ids["tecnico"] = None
        if Tecnico.objects.filter(id=tecnico_id).exists():
            raise AssertionError("Tecnico delete validation failed")

        return {
            "ok": True,
            "checks": {
                "clientes": "create/update/delete ok",
                "cuentas": "create/update/delete ok",
                "inventario": "create/update/delete ok",
                "tecnicos": "create/update/delete ok",
            },
            "actors": {
                "username": username,
            },
        }
    finally:
        # Cleanup keeps script idempotent even after partial failures.
        if created_ids["cuenta"] and Cuenta.objects.filter(id=created_ids["cuenta"]).exists():
            Cuenta.objects.filter(id=created_ids["cuenta"]).delete()
        if created_ids["cliente"] and Cliente.objects.filter(id=created_ids["cliente"]).exists():
            Cliente.objects.filter(id=created_ids["cliente"]).delete()
        if created_ids["inventario"] and ItemInventario.objects.filter(id=created_ids["inventario"]).exists():
            ItemInventario.objects.filter(id=created_ids["inventario"]).delete()
        if created_ids["tecnico"] and Tecnico.objects.filter(id=created_ids["tecnico"]).exists():
            Tecnico.objects.filter(id=created_ids["tecnico"]).delete()
        if created_ids["user"] and User.objects.filter(id=created_ids["user"]).exists():
            User.objects.filter(id=created_ids["user"]).delete()


if __name__ == "__main__":
    try:
        output = run_verification()
        print(json.dumps(output, ensure_ascii=True, indent=2, default=str))
        sys.exit(0)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=True, indent=2))
        sys.exit(1)

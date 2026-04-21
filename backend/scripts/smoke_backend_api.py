import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.contrib.auth.models import Group  # noqa: E402
from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402

from apps.clientes.models import Cliente  # noqa: E402
from apps.cuentas.models import Cuenta  # noqa: E402
from apps.pedidos.models import Pedido  # noqa: E402
from apps.tecnicos.models import Tecnico  # noqa: E402


User = get_user_model()


def assert_status(response, expected_status, context):
    if response.status_code != expected_status:
        detail = getattr(response, "data", response.content.decode("utf-8", errors="ignore"))
        raise AssertionError(
            f"{context}: expected {expected_status}, got {response.status_code}. Detail: {detail}"
        )


def reset_test_data():
    Pedido.objects.all().delete()
    Cuenta.objects.all().delete()
    Cliente.objects.all().delete()
    Tecnico.objects.all().delete()

    User.objects.filter(username__in=["coord_seed", "tech_seed"]).delete()


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
        raise AssertionError(f"Login user {username}: no access token returned")
    return token


def auth_client(token):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def unwrap_list_payload(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return payload.get("results", [])
    return []


def run_smoke_test():
    reset_test_data()

    coord_password = "Coord12345!"
    tech_password = "Tech12345!"

    coord_group, _ = Group.objects.get_or_create(name="coordinador")

    coord_user = User.objects.create_user(
        username="coord_seed",
        password=coord_password,
        email="coord_seed@example.com",
    )
    coord_user.groups.add(coord_group)

    tech_user = User.objects.create_user(
        username="tech_seed",
        password=tech_password,
        email="tech_seed@example.com",
    )

    tecnico = Tecnico.objects.create(
        user=tech_user,
        nombre="Luis Rojas",
        especialidad="Electrico industrial",
        zona="Miraflores",
        latitud_base=-12.1211,
        longitud_base=-77.0297,
        capacidad_diaria=5,
        activo=True,
    )

    cliente = Cliente.objects.create(
        nombre="Clinica Miraflores",
        documento="20548796321",
        telefono="987123111",
        correo="laura.medina@clinicamf.pe",
        direccion="Av. Arequipa 1001",
        activo=True,
    )

    cuenta = Cuenta.objects.create(
        cliente=cliente,
        nombre="Sede Principal",
        numero="CUE-1001",
        tipo=Cuenta.TipoCuenta.EMPRESA,
        latitud=-12.1211,
        longitud=-77.0297,
        activa=True,
    )

    coord_token = login_and_get_token("coord_seed", coord_password)
    tech_token = login_and_get_token("tech_seed", tech_password)

    coord_client = auth_client(coord_token)
    tech_client = auth_client(tech_token)

    me_coord = coord_client.get("/api/auth/me/")
    assert_status(me_coord, 200, "GET /api/auth/me coordinador")

    me_tech = tech_client.get("/api/auth/me/")
    assert_status(me_tech, 200, "GET /api/auth/me tecnico")

    create_payload = {
        "cliente": str(cliente.id),
        "cuenta": str(cuenta.id),
        "titulo": "Mantenimiento electrico integral",
        "descripcion": "Prueba end-to-end del flujo tecnico",
        "tipo_servicio": "mantenimiento electrico",
        "zona": "Miraflores",
        "prioridad": "alta",
    }

    create_resp = coord_client.post("/api/pedidos/", create_payload, format="json")
    assert_status(create_resp, 201, "POST /api/pedidos")
    pedido_id = create_resp.data["id"]

    auto_resp = coord_client.post(f"/api/pedidos/{pedido_id}/auto_asignar/", {}, format="json")
    assert_status(auto_resp, 200, "POST /api/pedidos/{id}/auto_asignar")

    if not auto_resp.data.get("auto_asignado"):
        raise AssertionError("Auto asignacion no asigno tecnico")

    mis_asignados_resp = tech_client.get("/api/pedidos/mis-asignados/")
    assert_status(mis_asignados_resp, 200, "GET /api/pedidos/mis-asignados")
    if not any(item["id"] == pedido_id for item in mis_asignados_resp.data):
        raise AssertionError("Pedido no aparece en mis-asignados para tecnico")

    confirm_resp = tech_client.post(f"/api/pedidos/{pedido_id}/confirmar-tecnico/", {}, format="json")
    assert_status(confirm_resp, 200, "POST /api/pedidos/{id}/confirmar-tecnico")

    checklist_steps = [
        ("materiales-listos", "Materiales listos"),
        ("llegada-sitio", "Llegada al sitio"),
        ("inicio-trabajo", "Inicio de trabajo"),
        ("nota-adicional", "Se realiza inspeccion sin novedades"),
    ]

    for step_id, note in checklist_steps:
        payload = {"step_id": step_id, "completado": True, "nota": note}
        step_resp = tech_client.post(f"/api/pedidos/{pedido_id}/checklist/", payload, format="json")
        if step_resp.status_code not in (200, 201):
            detail = getattr(step_resp, "data", step_resp.content.decode("utf-8", errors="ignore"))
            raise AssertionError(
                f"POST /api/pedidos/{pedido_id}/checklist/ {step_id} fallo: {detail}"
            )

    evidencia_antes = SimpleUploadedFile("antes.jpg", b"fake-image-antes", content_type="image/jpeg")
    ev_before_resp = tech_client.post(
        f"/api/pedidos/{pedido_id}/evidencias/",
        {
            "archivo": evidencia_antes,
            "descripcion": "Tablero antes de intervencion",
            "stage": "antes",
            "source": "archivo",
        },
        format="multipart",
    )
    assert_status(ev_before_resp, 201, "POST evidencias antes")

    evidencia_despues = SimpleUploadedFile("despues.jpg", b"fake-image-despues", content_type="image/jpeg")
    ev_after_resp = tech_client.post(
        f"/api/pedidos/{pedido_id}/evidencias/",
        {
            "archivo": evidencia_despues,
            "descripcion": "Tablero despues de intervencion",
            "stage": "despues",
            "source": "archivo",
        },
        format="multipart",
    )
    assert_status(ev_after_resp, 201, "POST evidencias despues")

    diag_resp = tech_client.patch(
        f"/api/pedidos/{pedido_id}/diagnostico/",
        {"diagnostico_tecnico": "Diagnostico tecnico final validado"},
        format="json",
    )
    assert_status(diag_resp, 200, "PATCH /api/pedidos/{id}/diagnostico")

    firma = SimpleUploadedFile("firma.png", b"fake-signature", content_type="image/png")
    report_resp = tech_client.post(
        f"/api/pedidos/{pedido_id}/informe-tecnico/",
        {
            "diagnostico_final": "Diagnostico final completado",
            "responsable_local": "Laura Medina",
            "pedido_solicitado": "Mantenimiento electrico integral",
            "observaciones": "Se corrige sobrecarga y cableado",
            "recomendaciones": "Monitoreo mensual",
            "firma_cliente": firma,
        },
        format="multipart",
    )
    if report_resp.status_code not in (200, 201):
        detail = getattr(report_resp, "data", report_resp.content.decode("utf-8", errors="ignore"))
        raise AssertionError(f"POST informe tecnico fallo: {detail}")

    final_resp = coord_client.get(f"/api/pedidos/{pedido_id}/")
    assert_status(final_resp, 200, "GET /api/pedidos/{id} final")

    final_data = final_resp.data
    if final_data.get("status_operativo") != Pedido.StatusOperativo.COMPLETADO:
        raise AssertionError("El pedido no quedo en status_operativo=completado")
    if final_data.get("fase") != Pedido.Fase.CIERRE:
        raise AssertionError("El pedido no quedo en fase=cierre")

    baja_payload = {
        "cliente": str(cliente.id),
        "cuenta": str(cuenta.id),
        "titulo": "Pedido para prueba de baja",
        "descripcion": "Se usa para validar la accion dar-baja",
        "tipo_servicio": "inspeccion",
        "zona": "Miraflores",
        "prioridad": "media",
    }
    baja_create_resp = coord_client.post("/api/pedidos/", baja_payload, format="json")
    assert_status(baja_create_resp, 201, "POST /api/pedidos (baja)")
    baja_pedido_id = baja_create_resp.data["id"]

    baja_resp = coord_client.post(
        f"/api/pedidos/{baja_pedido_id}/dar-baja/",
        {"motivo": "Solicitud cancelada por cliente"},
        format="json",
    )
    assert_status(baja_resp, 200, "POST /api/pedidos/{id}/dar-baja")
    if baja_resp.data.get("status_operativo") != Pedido.StatusOperativo.DADO_DE_BAJA:
        raise AssertionError("La accion dar-baja no actualizo status_operativo")

    list_default_resp = coord_client.get("/api/pedidos/")
    assert_status(list_default_resp, 200, "GET /api/pedidos/ default")
    list_default_items = unwrap_list_payload(list_default_resp.data)
    if any(item["id"] == baja_pedido_id for item in list_default_items):
        raise AssertionError("Pedido dado de baja no debe aparecer en listado default")

    list_with_bajas_resp = coord_client.get("/api/pedidos/?include_bajas=1")
    assert_status(list_with_bajas_resp, 200, "GET /api/pedidos/?include_bajas=1")
    list_with_bajas_items = unwrap_list_payload(list_with_bajas_resp.data)
    if not any(item["id"] == baja_pedido_id for item in list_with_bajas_items):
        raise AssertionError("Pedido dado de baja no aparece cuando include_bajas=1")

    result = {
        "ok": True,
        "pedido_id": pedido_id,
        "pedido_baja_id": baja_pedido_id,
        "coordinador_role": me_coord.data.get("role"),
        "tecnico_role": me_tech.data.get("role"),
        "final_status_operativo": final_data.get("status_operativo"),
        "final_subfase_tecnica": final_data.get("subfase_tecnica"),
        "final_fase": final_data.get("fase"),
        "baja_status_operativo": baja_resp.data.get("status_operativo"),
        "historial_items": len(final_data.get("historial", [])),
        "checklist_items": len(final_data.get("checklist_steps", [])),
        "evidencias_items": len(final_data.get("evidencias", [])),
        "has_informe_tecnico": final_data.get("informe_tecnico") is not None,
    }
    return result


if __name__ == "__main__":
    try:
        output = run_smoke_test()
        print(json.dumps(output, ensure_ascii=True, indent=2))
        sys.exit(0)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=True, indent=2))
        sys.exit(1)

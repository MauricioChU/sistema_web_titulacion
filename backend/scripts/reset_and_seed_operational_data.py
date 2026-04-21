import argparse
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
from django.core.management import call_command  # noqa: E402
from pymongo import MongoClient  # noqa: E402

from apps.clientes.models import Cliente  # noqa: E402
from apps.cuentas.models import Cuenta  # noqa: E402
from apps.inventario.models import ItemInventario  # noqa: E402
from apps.pedidos.models import Pedido  # noqa: E402
from apps.tecnicos.models import Tecnico  # noqa: E402


User = get_user_model()


def _mongo_conf():
    return {
        "mongo_uri": os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017").strip(),
        "mongo_db_name": os.getenv("MONGODB_DB_NAME", "sistema_titulacion").strip(),
        "timeout_ms": int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "3000")),
        "sync_enabled": os.getenv("MONGODB_SYNC_ENABLED", "true").strip().lower()
        not in {"0", "false", "no", "off"},
        "collections": {
            "pedidos": os.getenv("MONGODB_PEDIDOS_COLLECTION", "pedidos").strip() or "pedidos",
            "clientes": os.getenv("MONGODB_CLIENTES_COLLECTION", "clientes").strip() or "clientes",
            "cuentas": os.getenv("MONGODB_CUENTAS_COLLECTION", "cuentas").strip() or "cuentas",
            "tecnicos": os.getenv("MONGODB_TECNICOS_COLLECTION", "tecnicos").strip() or "tecnicos",
            "inventario": os.getenv("MONGODB_INVENTARIO_COLLECTION", "inventario").strip() or "inventario",
            "usuarios": os.getenv("MONGODB_USUARIOS_COLLECTION", "usuarios").strip() or "usuarios",
        },
    }


def _mongo_client(conf):
    client = MongoClient(conf["mongo_uri"], serverSelectionTimeoutMS=conf["timeout_ms"])
    client.admin.command("ping")
    return client


def _role_for_user(user, tecnico=None):
    if user.is_superuser:
        return "admin"
    if tecnico is not None:
        return "tecnico"
    if user.is_staff or user.groups.filter(name__iexact="coordinador").exists():
        return "coordinador"
    return "usuario"


def drop_mongo_databases(conf, target_db: str, drop_legacy: bool):
    client = _mongo_client(conf)
    db_names_before = set(client.list_database_names())

    dropped_target = target_db in db_names_before
    client.drop_database(target_db)

    dropped_legacy = False
    if drop_legacy and "titulacion_db" in db_names_before:
        client.drop_database("titulacion_db")
        dropped_legacy = True

    client.close()
    return {
        "mongo_uri": conf["mongo_uri"],
        "target_db": target_db,
        "dropped_target_db": dropped_target,
        "dropped_legacy_titulacion_db": dropped_legacy,
    }


def run_migrations():
    call_command("migrate", interactive=False, verbosity=0)


def clear_domain_data():
    deleted_counts = {
        "pedidos": Pedido.objects.count(),
        "inventario": ItemInventario.objects.count(),
        "cuentas": Cuenta.objects.count(),
        "clientes": Cliente.objects.count(),
        "tecnicos": Tecnico.objects.count(),
        "usuarios": User.objects.count(),
        "grupos": Group.objects.count(),
    }

    Pedido.objects.all().delete()
    ItemInventario.objects.all().delete()
    Cuenta.objects.all().delete()
    Cliente.objects.all().delete()
    Tecnico.objects.all().delete()
    User.objects.all().delete()
    Group.objects.all().delete()

    return deleted_counts


def seed_base_data():
    coordinador_group = Group.objects.create(name="coordinador")

    admin_user = User.objects.create_user(
        username="admin",
        password="admin123",
        email="admin@example.com",
        is_staff=True,
        is_superuser=True,
    )

    coord_user = User.objects.create_user(
        username="coordinador",
        password="admin123",
        email="coordinador@example.com",
        is_staff=True,
        is_superuser=False,
    )
    coord_user.groups.add(coordinador_group)

    tecnico_user = User.objects.create_user(
        username="tecnico",
        password="admin123",
        email="tecnico@example.com",
        is_staff=False,
        is_superuser=False,
    )

    tecnico_base = Tecnico.objects.create(
        user=tecnico_user,
        nombre="Tecnico Base",
        especialidad="general",
        zona="Lima Centro",
        latitud_base=-12.0464,
        longitud_base=-77.0428,
        capacidad_diaria=5,
        activo=True,
    )
    tecnico_luis = Tecnico.objects.create(
        nombre="Luis Rojas",
        especialidad="electrico industrial",
        zona="Miraflores",
        latitud_base=-12.1211,
        longitud_base=-77.0297,
        capacidad_diaria=5,
        activo=True,
    )
    tecnico_martha = Tecnico.objects.create(
        nombre="Martha Pino",
        especialidad="cableado estructurado",
        zona="San Isidro",
        latitud_base=-12.0962,
        longitud_base=-77.0307,
        capacidad_diaria=4,
        activo=True,
    )

    cliente_1 = Cliente.objects.create(
        nombre="Clinica Horizonte",
        documento="20999111222",
        telefono="987111222",
        correo="contacto@clinicahorizonte.pe",
        direccion="Av. Primavera 1200",
        activo=True,
    )
    cliente_2 = Cliente.objects.create(
        nombre="Condominio Alameda",
        documento="20666677778",
        telefono="965123456",
        correo="admin@alameda.pe",
        direccion="Jr. Los Pinos 550",
        activo=True,
    )
    cliente_3 = Cliente.objects.create(
        nombre="Retail Centro SAC",
        documento="20123456789",
        telefono="955888444",
        correo="soporte@retailcentro.com",
        direccion="Av. Central 450",
        activo=True,
    )

    Cuenta.objects.create(
        cliente=cliente_1,
        nombre="Sede Principal",
        numero="CUE-5001",
        direccion="Av. Primavera 1200",
        contacto="Mesa de ayuda Horizonte",
        telefono="987111222",
        tipo=Cuenta.TipoCuenta.EMPRESA,
        latitud=-12.1211,
        longitud=-77.0297,
        activa=True,
    )
    Cuenta.objects.create(
        cliente=cliente_1,
        nombre="Sede Secundaria",
        numero="CUE-5002",
        direccion="Av. Primavera 1300",
        contacto="Recepcion Horizonte",
        telefono="987111223",
        tipo=Cuenta.TipoCuenta.EMPRESA,
        latitud=-12.1308,
        longitud=-77.0272,
        activa=True,
    )
    Cuenta.objects.create(
        cliente=cliente_2,
        nombre="Torre A",
        numero="CUE-6001",
        direccion="Jr. Los Pinos 550",
        contacto="Administracion Torre A",
        telefono="965123456",
        tipo=Cuenta.TipoCuenta.HOGAR,
        latitud=-12.1405,
        longitud=-76.9910,
        activa=True,
    )
    Cuenta.objects.create(
        cliente=cliente_3,
        nombre="Local Centro",
        numero="CUE-7001",
        direccion="Av. Central 450",
        contacto="Soporte Retail Centro",
        telefono="955888444",
        tipo=Cuenta.TipoCuenta.EMPRESA,
        latitud=-12.0962,
        longitud=-77.0307,
        activa=True,
    )

    items = [
        {"sku": "EPP-CAS-001", "descripcion": "Casco de seguridad dielectrico", "categoria": "epp", "stock": 40, "stock_minimo": 10, "unidad_medida": "unidad", "almacen": "principal", "activo": True},
        {"sku": "EPP-GUA-002", "descripcion": "Guantes aislantes clase 00", "categoria": "epp", "stock": 60, "stock_minimo": 15, "unidad_medida": "par", "almacen": "principal", "activo": True},
        {"sku": "HER-MUL-003", "descripcion": "Multimetro digital", "categoria": "herramienta", "stock": 18, "stock_minimo": 6, "unidad_medida": "unidad", "almacen": "principal", "activo": True},
        {"sku": "HER-PEL-004", "descripcion": "Pelacables profesional", "categoria": "herramienta", "stock": 22, "stock_minimo": 8, "unidad_medida": "unidad", "almacen": "principal", "activo": True},
        {"sku": "MAT-CAB-005", "descripcion": "Cable UTP Cat6 305m", "categoria": "material", "stock": 25, "stock_minimo": 7, "unidad_medida": "rollo", "almacen": "sur", "activo": True},
        {"sku": "MAT-CAN-006", "descripcion": "Canaleta PVC 40x20", "categoria": "material", "stock": 120, "stock_minimo": 30, "unidad_medida": "unidad", "almacen": "sur", "activo": True},
        {"sku": "MAT-UPS-007", "descripcion": "Bateria UPS 12V 9Ah", "categoria": "material", "stock": 35, "stock_minimo": 10, "unidad_medida": "unidad", "almacen": "norte", "activo": True},
        {"sku": "EPP-CHA-008", "descripcion": "Chaleco reflectivo clase 2", "categoria": "epp", "stock": 55, "stock_minimo": 12, "unidad_medida": "unidad", "almacen": "norte", "activo": True},
    ]
    for item in items:
        ItemInventario.objects.create(**item)

    return {
        "users": {
            "admin": admin_user,
            "coordinador": coord_user,
            "tecnico": tecnico_user,
        },
        "tecnicos_by_user": {
            str(tecnico_user.id): tecnico_base,
        },
        "counts": {
            "usuarios": User.objects.count(),
            "grupos": Group.objects.count(),
            "clientes": Cliente.objects.count(),
            "cuentas": Cuenta.objects.count(),
            "tecnicos": Tecnico.objects.count(),
            "inventario": ItemInventario.objects.count(),
            "pedidos": Pedido.objects.count(),
        },
        "credentials": {
            "admin": "admin123",
            "coordinador": "admin123",
            "tecnico": "admin123",
        },
        "tecnicos_seed": [str(tecnico_base.id), str(tecnico_luis.id), str(tecnico_martha.id)],
    }


def sync_usuarios_collection(conf, target_db: str, seed_context):
    client = _mongo_client(conf)
    users_col = client[target_db][conf["collections"]["usuarios"]]

    upserts = 0
    try:
        for _, user in seed_context["users"].items():
            tecnico = seed_context["tecnicos_by_user"].get(str(user.id))
            role = _role_for_user(user, tecnico)
            doc = {
                "_id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "role": role,
                "tecnico_id": getattr(tecnico, "id", None),
                "tecnico_nombre": getattr(tecnico, "nombre", None),
                "seed_tag": "reset_and_seed_operational_data",
            }
            users_col.update_one({"_id": user.id}, {"$set": doc}, upsert=True)
            upserts += 1

        return {
            "collection": conf["collections"]["usuarios"],
            "upserts": upserts,
            "count": users_col.count_documents({}),
        }
    finally:
        client.close()


def mongo_snapshot(conf, target_db: str):
    client = _mongo_client(conf)
    db = client[target_db]

    try:
        counts = {}
        for key, collection in conf["collections"].items():
            counts[key] = db[collection].count_documents({})

        return {
            "db": target_db,
            "collections": sorted(db.list_collection_names()),
            "counts": counts,
        }
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(
        description="Limpia completamente Mongo, migra y genera seed base sin pedidos"
    )
    parser.add_argument(
        "--mongo-db",
        default="",
        help="Base Mongo objetivo. Si se omite, usa MONGODB_DB_NAME.",
    )
    parser.add_argument(
        "--drop-legacy-db",
        action="store_true",
        help="Eliminar la base legacy titulacion_db para evitar confusiones",
    )
    parser.add_argument(
        "--empty-only",
        action="store_true",
        help="Solo limpiar datos (Mongo + migraciones) sin sembrar registros",
    )
    args = parser.parse_args()

    conf = _mongo_conf()
    target_db = (args.mongo_db or conf["mongo_db_name"]).strip() or "sistema_titulacion"

    mongo_drop_result = drop_mongo_databases(
        conf=conf,
        target_db=target_db,
        drop_legacy=args.drop_legacy_db,
    )

    run_migrations()
    deleted_before_seed = clear_domain_data()

    if args.empty_only:
        seed_counts = {
            "usuarios": 0,
            "grupos": 0,
            "clientes": 0,
            "cuentas": 0,
            "tecnicos": 0,
            "inventario": 0,
            "pedidos": 0,
        }
        usuarios_sync = {
            "collection": conf["collections"]["usuarios"],
            "upserts": 0,
            "count": 0,
        }
        credentials = {}
        tecnicos_seed = []
    else:
        seed_context = seed_base_data()
        usuarios_sync = sync_usuarios_collection(conf=conf, target_db=target_db, seed_context=seed_context)
        seed_counts = seed_context["counts"]
        credentials = seed_context["credentials"]
        tecnicos_seed = seed_context["tecnicos_seed"]

    snapshot = mongo_snapshot(conf=conf, target_db=target_db)

    output = {
        "ok": True,
        "empty_only": args.empty_only,
        "sync_enabled": conf["sync_enabled"],
        "deleted_before_seed": deleted_before_seed,
        "seeded": seed_counts,
        "usuarios_sync": usuarios_sync,
        "tecnicos_seed_ids": tecnicos_seed,
        "credentials": credentials,
        "mongo_drop": mongo_drop_result,
        "mongo_snapshot": snapshot,
        "assertions": {
            "pedidos_vacios": Pedido.objects.count() == 0,
            "usuarios_base_creados": User.objects.count() == 3 if not args.empty_only else True,
            "inventario_con_datos": ItemInventario.objects.count() > 0 if not args.empty_only else True,
        },
    }
    print(json.dumps(output, ensure_ascii=True, indent=2, default=str))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=True, indent=2))
        sys.exit(1)

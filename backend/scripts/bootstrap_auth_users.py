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
from pymongo import MongoClient  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402

from apps.tecnicos.models import Tecnico  # noqa: E402


User = get_user_model()


def _mongo_client():
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017").strip()
    timeout_ms = int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "3000"))
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=timeout_ms)
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


def _create_or_update_user(username, password, email, is_staff=False, is_superuser=False):
    user, created = User.objects.get_or_create(username=username, defaults={"email": email})
    user.email = email
    user.is_staff = is_staff
    user.is_superuser = is_superuser
    user.set_password(password)
    user.save()
    return user, created


def _upsert_usuario_doc(collection, user, role, tecnico=None):
    doc = {
        "_id": user.id,
        "username": user.username,
        "email": user.email,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "role": role,
        "tecnico_id": getattr(tecnico, "id", None),
        "tecnico_nombre": getattr(tecnico, "nombre", None),
    }
    collection.update_one({"_id": user.id}, {"$set": doc}, upsert=True)


def _verify_login(username, password):
    api = APIClient()
    login_resp = api.post("/api/auth/login/", {"username": username, "password": password}, format="json")
    if login_resp.status_code != 200:
        detail = getattr(login_resp, "data", login_resp.content.decode("utf-8", errors="ignore"))
        raise AssertionError(f"Login fallo para {username}: {detail}")

    token = login_resp.data.get("access")
    if not token:
        raise AssertionError(f"Login de {username} no devolvio access token")

    me_client = APIClient()
    me_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    me_resp = me_client.get("/api/auth/me/")
    if me_resp.status_code != 200:
        detail = getattr(me_resp, "data", me_resp.content.decode("utf-8", errors="ignore"))
        raise AssertionError(f"GET /api/auth/me fallo para {username}: {detail}")
    return me_resp.data


def main():
    coordinador_group, _ = Group.objects.get_or_create(name="coordinador")

    admin_user, admin_created = _create_or_update_user(
        username="admin",
        password="admin123",
        email="admin@example.com",
        is_staff=True,
        is_superuser=True,
    )

    coord_user, coord_created = _create_or_update_user(
        username="coordinador",
        password="admin123",
        email="coordinador@example.com",
        is_staff=True,
        is_superuser=False,
    )
    coord_user.groups.add(coordinador_group)

    tecnico_user, tecnico_created = _create_or_update_user(
        username="tecnico",
        password="admin123",
        email="tecnico@example.com",
        is_staff=False,
        is_superuser=False,
    )
    tecnico_user.groups.remove(coordinador_group)

    tecnico_obj, tecnico_profile_created = Tecnico.objects.get_or_create(
        user=tecnico_user,
        defaults={
            "nombre": "Tecnico Base",
            "especialidad": "general",
            "zona": "Lima",
            "latitud_base": -12.0464,
            "longitud_base": -77.0428,
            "capacidad_diaria": 5,
            "activo": True,
        },
    )
    if not tecnico_profile_created:
        tecnico_obj.latitud_base = tecnico_obj.latitud_base if tecnico_obj.latitud_base is not None else -12.0464
        tecnico_obj.longitud_base = tecnico_obj.longitud_base if tecnico_obj.longitud_base is not None else -77.0428
        tecnico_obj.save(update_fields=["latitud_base", "longitud_base", "updated_at"])

    mongo_db_name = os.getenv("MONGODB_DB_NAME", "sistema_titulacion").strip()
    usuarios_collection = os.getenv("MONGODB_USUARIOS_COLLECTION", "usuarios").strip() or "usuarios"

    client = _mongo_client()
    try:
        usuarios_col = client[mongo_db_name][usuarios_collection]
        _upsert_usuario_doc(usuarios_col, admin_user, _role_for_user(admin_user))
        _upsert_usuario_doc(usuarios_col, coord_user, _role_for_user(coord_user))
        _upsert_usuario_doc(usuarios_col, tecnico_user, _role_for_user(tecnico_user, tecnico_obj), tecnico_obj)
    finally:
        client.close()

    admin_me = _verify_login("admin", "admin123")
    coord_me = _verify_login("coordinador", "admin123")
    tecnico_me = _verify_login("tecnico", "admin123")

    output = {
        "ok": True,
        "mongo_db": mongo_db_name,
        "usuarios_collection": usuarios_collection,
        "users": {
            "admin": {
                "created": admin_created,
                "username": admin_user.username,
                "role": admin_me.get("role"),
            },
            "coordinador": {
                "created": coord_created,
                "username": coord_user.username,
                "role": coord_me.get("role"),
            },
            "tecnico": {
                "created": tecnico_created,
                "username": tecnico_user.username,
                "role": tecnico_me.get("role"),
                "tecnico_profile_created": tecnico_profile_created,
                "tecnico_id": tecnico_me.get("tecnico_id"),
                "latitud_base": tecnico_obj.latitud_base,
                "longitud_base": tecnico_obj.longitud_base,
            },
        },
        "credentials": {
            "admin": "admin123",
            "coordinador": "admin123",
            "tecnico": "admin123",
        },
    }
    print(json.dumps(output, ensure_ascii=True, indent=2, default=str))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=True, indent=2))
        sys.exit(1)
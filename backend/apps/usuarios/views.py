from __future__ import annotations

from datetime import datetime, timezone

from django.contrib.auth.hashers import make_password
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.db import get_db
from apps.core.helpers import (
    bad_request, created, no_content, not_found, ok,
    require_oid, serialize_doc, serialize_docs,
)
from apps.core.permissions import EsAdmin, EsSupervisorOAdmin

ROLES_VALIDOS = ("admin", "coordinador", "tecnico")
PRIVILEGIOS_VALIDOS = (None, "supervisor")


class UsuarioListView(APIView):
    """GET  /api/usuarios/   → listar  (admin y supervisor)
       POST /api/usuarios/   → crear   (solo admin)"""

    def get_permissions(self):
        if self.request.method == "POST":
            return [EsAdmin()]
        return [EsSupervisorOAdmin()]

    def get(self, request):
        db = get_db()
        filtro: dict = {}
        rol = request.query_params.get("rol")
        if rol:
            filtro["rol"] = rol
        activo = request.query_params.get("activo")
        if activo is not None:
            filtro["activo"] = activo.lower() != "false"

        usuarios = list(db.users.find(filtro, {"password_hash": 0}).sort("nombre_completo", 1))
        return ok(serialize_docs(usuarios))

    def post(self, request):
        data = request.data
        errores = _validar_usuario(data, nuevo=True)
        if errores:
            return bad_request(errores)

        db = get_db()
        if db.users.find_one({"username": data["username"].strip().lower()}):
            return bad_request("El nombre de usuario ya existe.")

        rol = data["rol"]
        privilegio = data.get("privilegio") if rol == "coordinador" else None

        doc = {
            "username": data["username"].strip().lower(),
            "password_hash": make_password(data["password"]),
            "email": data.get("email", "").strip().lower(),
            "nombre_completo": data.get("nombre_completo", "").strip(),
            "rol": rol,
            "privilegio": privilegio,
            "activo": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        result = db.users.insert_one(doc)
        doc["_id"] = result.inserted_id

        # Si es técnico, crear perfil de técnico automáticamente
        if rol == "tecnico":
            db.tecnicos.insert_one({
                "user_id": result.inserted_id,
                "nombre": doc["nombre_completo"] or doc["username"],
                "especialidad": data.get("especialidad", "General"),
                "zona": data.get("zona", ""),
                "telefono": data.get("telefono", ""),
                "latitud_base": float(data.get("latitud_base", -12.0464)),
                "longitud_base": float(data.get("longitud_base", -77.0428)),
                "activo": True,
                "created_at": datetime.now(timezone.utc),
            })

        return created(serialize_doc({k: v for k, v in doc.items() if k != "password_hash"}))


class UsuarioDetailView(APIView):
    """GET/PUT/DELETE /api/usuarios/{id}/"""

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [EsAdmin()]
        return [EsSupervisorOAdmin()]

    def _get_user(self, uid: str):
        oid = require_oid(uid, "id")
        db = get_db()
        return db.users.find_one({"_id": oid})

    def get(self, request, pk):
        user = self._get_user(pk)
        if not user:
            return not_found("Usuario no encontrado.")
        user.pop("password_hash", None)
        return ok(serialize_doc(user))

    def put(self, request, pk):
        try:
            oid = require_oid(pk, "id")
        except ValueError as e:
            return bad_request(str(e))

        db = get_db()
        user = db.users.find_one({"_id": oid})
        if not user:
            return not_found("Usuario no encontrado.")

        data = request.data
        update: dict = {"updated_at": datetime.now(timezone.utc)}

        if "nombre_completo" in data:
            update["nombre_completo"] = data["nombre_completo"].strip()
        if "email" in data:
            update["email"] = data["email"].strip().lower()
        if "password" in data and data["password"]:
            update["password_hash"] = make_password(data["password"])
        if "activo" in data:
            update["activo"] = bool(data["activo"])
        if "privilegio" in data and user.get("rol") == "coordinador":
            p = data["privilegio"]
            update["privilegio"] = p if p in ("supervisor",) else None
        if "especialidad" in data:
            update["especialidad"] = data["especialidad"]
        if "zona" in data:
            update["zona"] = data["zona"]
        if "telefono" in data:
            update["telefono"] = data["telefono"]

        # Sync técnico perfil si aplica
        if user.get("rol") == "tecnico":
            tecnico_update: dict = {}
            for campo in ("especialidad", "zona", "telefono", "latitud_base", "longitud_base"):
                if campo in data:
                    tecnico_update[campo] = data[campo]
            if "nombre_completo" in data:
                tecnico_update["nombre"] = data["nombre_completo"].strip()
            if tecnico_update:
                db.tecnicos.update_one({"user_id": oid}, {"$set": tecnico_update})

        db.users.update_one({"_id": oid}, {"$set": update})
        updated = db.users.find_one({"_id": oid}, {"password_hash": 0})
        return ok(serialize_doc(updated))

    def delete(self, request, pk):
        try:
            oid = require_oid(pk, "id")
        except ValueError as e:
            return bad_request(str(e))

        db = get_db()
        user = db.users.find_one({"_id": oid})
        if not user:
            return not_found("Usuario no encontrado.")

        # Desactivar en vez de eliminar (conservar historial)
        db.users.update_one({"_id": oid}, {"$set": {"activo": False, "updated_at": datetime.now(timezone.utc)}})
        if user.get("rol") == "tecnico":
            db.tecnicos.update_one({"user_id": oid}, {"$set": {"activo": False}})
        return no_content()


def _validar_usuario(data: dict, nuevo: bool) -> str | None:
    if nuevo:
        for campo in ("username", "password", "rol"):
            if not data.get(campo):
                return f"'{campo}' es requerido."
    if "rol" in data and data["rol"] not in ROLES_VALIDOS:
        return f"Rol inválido. Opciones: {ROLES_VALIDOS}"
    return None

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.contrib.auth.hashers import check_password
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.core.db import get_db
from apps.core.helpers import bad_request, ok, serialize_doc


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = (request.data.get("username") or "").strip().lower()
        password = request.data.get("password") or ""

        if not username or not password:
            return bad_request("Usuario y contraseña son requeridos.")

        db = get_db()
        user = db.users.find_one({"username": username, "activo": True})
        if not user or not check_password(password, user["password_hash"]):
            return bad_request("Credenciales incorrectas.")

        token_str = str(uuid.uuid4())
        ttl = getattr(settings, "TOKEN_TTL_HOURS", 24)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl)

        db.tokens.insert_one({
            "token": token_str,
            "user_id": user["_id"],
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc),
        })

        return ok({
            "token": token_str,
            "expires_at": expires_at.isoformat() + "Z",
            "user": _format_user(user),
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.auth
        if token:
            get_db().tokens.delete_one({"token": token})
        return ok({"detail": "Sesión cerrada."})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return ok(_format_user(request.user))


def _format_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "nombre_completo": user.get("nombre_completo", ""),
        "email": user.get("email", ""),
        "rol": user.get("rol", ""),
        "privilegio": user.get("privilegio"),
        "avatar": user.get("avatar"),
    }

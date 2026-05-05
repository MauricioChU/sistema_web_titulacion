from __future__ import annotations

from datetime import datetime, timezone

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from apps.core.db import get_db


class MongoUser:
    """Thin wrapper so DRF's IsAuthenticated can call .is_authenticated."""

    is_authenticated = True
    is_anonymous = False

    def __init__(self, doc: dict):
        self._doc = doc

    def __getitem__(self, key):
        return self._doc[key]

    def get(self, key, default=None):
        return self._doc.get(key, default)

    def __contains__(self, key):
        return key in self._doc

    def __repr__(self):
        return f"<MongoUser {self._doc.get('username')}>"


class MongoTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return None

        token_str = header[7:].strip()
        if not token_str:
            return None

        db = get_db()
        now = datetime.now(timezone.utc)

        token_doc = db.tokens.find_one(
            {"token": token_str, "expires_at": {"$gt": now}}
        )
        if not token_doc:
            raise AuthenticationFailed("Token inválido o expirado.")

        user_doc = db.users.find_one({"_id": token_doc["user_id"], "activo": True})
        if not user_doc:
            raise AuthenticationFailed("Usuario inactivo o no encontrado.")

        return (MongoUser(user_doc), token_str)

    def authenticate_header(self, request) -> str:
        return "Bearer"

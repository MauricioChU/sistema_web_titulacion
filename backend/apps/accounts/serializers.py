from __future__ import annotations

from rest_framework import serializers

from .roles import resolve_role, tecnico_perfil


class SessionUserSerializer(serializers.Serializer):
    """Forma plana que consume el frontend en `/api/auth/me/`."""

    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField(allow_blank=True)
    is_staff = serializers.BooleanField()
    role = serializers.CharField()
    tecnico_id = serializers.IntegerField(allow_null=True)
    tecnico_nombre = serializers.CharField(allow_null=True)

    @classmethod
    def from_user(cls, user) -> dict:
        tecnico = tecnico_perfil(user)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email or "",
            "is_staff": bool(user.is_staff),
            "role": resolve_role(user),
            "tecnico_id": getattr(tecnico, "id", None),
            "tecnico_nombre": getattr(tecnico, "nombre", None),
        }

from __future__ import annotations

from rest_framework.permissions import BasePermission


class EsAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.get("rol") == "admin")


class EsCoordinadorOAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.get("rol") in ("admin", "coordinador"))


class EsTecnicoOAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.get("rol") in ("admin", "tecnico"))


class EsSupervisorOAdmin(BasePermission):
    """Coordinador con privilegio=supervisor, o admin."""
    def has_permission(self, request, view) -> bool:
        u = request.user
        if not u:
            return False
        if u.get("rol") == "admin":
            return True
        return u.get("rol") == "coordinador" and u.get("privilegio") == "supervisor"


class EsCoordinadorSupervisorOAdmin(BasePermission):
    """Admin o coordinador (cualquier nivel)."""
    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.get("rol") in ("admin", "coordinador"))


def rol_actual(user: dict) -> str:
    return user.get("rol", "")


def es_admin(user: dict) -> bool:
    return user.get("rol") == "admin"


def es_coordinador_o_admin(user: dict) -> bool:
    return user.get("rol") in ("admin", "coordinador")


def es_tecnico_o_admin(user: dict) -> bool:
    return user.get("rol") in ("admin", "tecnico")

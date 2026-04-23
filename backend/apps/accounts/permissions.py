"""Permisos reutilizables basados en roles."""
from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS

from .roles import is_coordinador_or_admin, resolve_role


class IsCoordinadorOrAdmin(BasePermission):
    """Solo coordinadores y admins pueden pasar."""

    message = "Solo coordinadores o administradores pueden ejecutar esta accion."

    def has_permission(self, request, view):
        return bool(request.user and is_coordinador_or_admin(request.user))


class ReadAllWriteCoordinador(BasePermission):
    """Lectura para cualquier usuario autenticado, escritura solo coord/admin."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return is_coordinador_or_admin(request.user)


class IsTecnico(BasePermission):
    """Requiere rol tecnico."""

    message = "Solo tecnicos pueden acceder a este recurso."

    def has_permission(self, request, view):
        return bool(request.user and resolve_role(request.user) == "tecnico")

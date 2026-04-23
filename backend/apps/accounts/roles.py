"""Resolucion y control de roles.

Reglas:
    - `admin`       -> user.is_superuser
    - `coordinador` -> user.is_staff o pertenece al grupo "coordinador"
    - `tecnico`     -> existe `user.tecnico_perfil`
    - `usuario`     -> el resto

Un solo lugar donde se decide el rol, para que no se duplique a lo largo de las views.
"""
from __future__ import annotations

from django.contrib.auth.models import AbstractUser

Role = str  # tipo semantico: "admin" | "coordinador" | "tecnico" | "usuario"


def tecnico_perfil(user: AbstractUser | None):
    """Devuelve el perfil tecnico asociado al usuario o None."""
    if user is None or not user.is_authenticated:
        return None
    try:
        return user.tecnico_perfil
    except Exception:
        return None


def resolve_role(user: AbstractUser | None) -> Role:
    if user is None or not user.is_authenticated:
        return "usuario"
    if getattr(user, "is_superuser", False):
        return "admin"
    if tecnico_perfil(user) is not None:
        return "tecnico"
    if getattr(user, "is_staff", False) or user.groups.filter(name__iexact="coordinador").exists():
        return "coordinador"
    return "usuario"


def is_coordinador_or_admin(user: AbstractUser | None) -> bool:
    return resolve_role(user) in {"coordinador", "admin"}

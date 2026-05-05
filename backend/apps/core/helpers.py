from __future__ import annotations

from datetime import datetime
from typing import Any

from bson import ObjectId
from rest_framework.response import Response
from rest_framework.views import exception_handler


# --------------------------------------------------------------------------- #
# Serialización MongoDB → JSON                                                #
# --------------------------------------------------------------------------- #

def _serialize_value(val: Any) -> Any:
    if isinstance(val, dict):
        return serialize_doc(val)
    if isinstance(val, list):
        return [_serialize_value(v) for v in val]
    if isinstance(val, ObjectId):
        return str(val)
    if isinstance(val, datetime):
        return val.isoformat() + ("Z" if val.tzinfo is None else "")
    return val


def serialize_doc(doc: dict | None) -> dict | None:
    if doc is None:
        return None
    out: dict = {}
    for key, val in doc.items():
        if key == "_id":
            out["id"] = str(val)
        else:
            out[key] = _serialize_value(val)
    return out


def serialize_docs(docs: list[dict]) -> list[dict]:
    return [serialize_doc(d) for d in docs]


# --------------------------------------------------------------------------- #
# ObjectId helpers                                                             #
# --------------------------------------------------------------------------- #

def to_oid(value: str | None) -> ObjectId | None:
    if not value:
        return None
    try:
        return ObjectId(value)
    except Exception:
        return None


def require_oid(value: str, field: str = "id") -> ObjectId:
    oid = to_oid(value)
    if oid is None:
        raise ValueError(f"'{field}' no es un ObjectId válido: {value!r}")
    return oid


# --------------------------------------------------------------------------- #
# Respuestas estándar                                                          #
# --------------------------------------------------------------------------- #

def ok(data: Any = None, status: int = 200) -> Response:
    return Response(data, status=status)


def created(data: Any) -> Response:
    return Response(data, status=201)


def no_content() -> Response:
    return Response(status=204)


def bad_request(msg: str) -> Response:
    return Response({"detail": msg}, status=400)


def not_found(msg: str = "No encontrado.") -> Response:
    return Response({"detail": msg}, status=404)


def forbidden(msg: str = "Sin permiso.") -> Response:
    return Response({"detail": msg}, status=403)


def conflict(msg: str) -> Response:
    return Response({"detail": msg}, status=409)


# --------------------------------------------------------------------------- #
# Exception handler global                                                     #
# --------------------------------------------------------------------------- #

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        return response
    return Response({"detail": str(exc)}, status=500)


# --------------------------------------------------------------------------- #
# Paginación simple                                                            #
# --------------------------------------------------------------------------- #

def paginate(data: list, page: int = 1, page_size: int = 50) -> dict:
    total = len(data)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "count": total,
        "page": page,
        "page_size": page_size,
        "results": data[start:end],
    }

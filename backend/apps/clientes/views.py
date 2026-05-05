from __future__ import annotations

from datetime import datetime, timezone

from rest_framework.views import APIView

from apps.core.db import get_db
from apps.core.helpers import (
    bad_request, created, no_content, not_found, ok,
    require_oid, serialize_doc, serialize_docs,
)
from apps.core.permissions import EsCoordinadorOAdmin


class ClienteListView(APIView):
    permission_classes = [EsCoordinadorOAdmin]

    def get(self, request):
        db = get_db()
        filtro: dict = {}
        activo_param = request.query_params.get("activo", "true").lower()
        if activo_param != "all":
            filtro["activo"] = activo_param != "false"
        q = request.query_params.get("q", "").strip()
        if q:
            import re
            regex = re.compile(re.escape(q), re.IGNORECASE)
            filtro["$or"] = [{"nombre": regex}, {"ruc": regex}]
        clientes = list(db.clientes.find(filtro).sort("nombre", 1))
        return ok(serialize_docs(clientes))

    def post(self, request):
        data = request.data
        if not data.get("nombre"):
            return bad_request("'nombre' es requerido.")

        db = get_db()
        ruc = data.get("ruc", "").strip()
        if ruc and db.clientes.find_one({"ruc": ruc}):
            return bad_request("Ya existe un cliente con ese RUC.")

        doc = {
            "nombre": data["nombre"].strip(),
            "ruc": ruc,
            "telefono": data.get("telefono", "").strip(),
            "correo": data.get("correo", "").strip().lower(),
            "direccion": data.get("direccion", "").strip(),
            "activo": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        result = db.clientes.insert_one(doc)
        doc["_id"] = result.inserted_id
        return created(serialize_doc(doc))


class ClienteDetailView(APIView):
    permission_classes = [EsCoordinadorOAdmin]

    def get(self, request, pk):
        try:
            oid = require_oid(pk)
        except ValueError as e:
            return bad_request(str(e))
        c = get_db().clientes.find_one({"_id": oid})
        if not c:
            return not_found("Cliente no encontrado.")
        return ok(serialize_doc(c))

    def put(self, request, pk):
        try:
            oid = require_oid(pk)
        except ValueError as e:
            return bad_request(str(e))

        db = get_db()
        if not db.clientes.find_one({"_id": oid}):
            return not_found()

        update: dict = {"updated_at": datetime.now(timezone.utc)}
        for field in ("nombre", "ruc", "telefono", "correo", "direccion"):
            if field in request.data:
                update[field] = request.data[field]
        if "activo" in request.data:
            update["activo"] = bool(request.data["activo"])

        db.clientes.update_one({"_id": oid}, {"$set": update})
        return ok(serialize_doc(db.clientes.find_one({"_id": oid})))

    def delete(self, request, pk):
        try:
            oid = require_oid(pk)
        except ValueError as e:
            return bad_request(str(e))

        db = get_db()
        if not db.clientes.find_one({"_id": oid}):
            return not_found()
        db.clientes.update_one({"_id": oid}, {"$set": {"activo": False, "updated_at": datetime.now(timezone.utc)}})
        return no_content()

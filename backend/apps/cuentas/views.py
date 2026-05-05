from __future__ import annotations

from datetime import datetime, timezone

from rest_framework.views import APIView

from apps.core.db import get_db
from apps.core.helpers import (
    bad_request, created, no_content, not_found, ok,
    require_oid, serialize_doc, serialize_docs, to_oid,
)
from apps.core.permissions import EsCoordinadorOAdmin

TIPOS_VALIDOS = ("empresa", "hogar", "gobierno", "otro")


class CuentaListView(APIView):
    permission_classes = [EsCoordinadorOAdmin]

    def get(self, request):
        db = get_db()
        filtro: dict = {}
        if "cliente_id" in request.query_params:
            oid = to_oid(request.query_params["cliente_id"])
            if oid:
                filtro["cliente_id"] = oid
        activo_param = request.query_params.get("activa", "true").lower()
        if activo_param != "all":
            filtro["activa"] = activo_param != "false"

        cuentas = list(db.cuentas.find(filtro).sort("nombre", 1))
        # Enriquecer con nombre de cliente
        cliente_ids = {c["cliente_id"] for c in cuentas if "cliente_id" in c}
        clientes_map = {
            c["_id"]: c["nombre"]
            for c in db.clientes.find({"_id": {"$in": list(cliente_ids)}}, {"nombre": 1})
        }
        for c in cuentas:
            c["cliente_nombre"] = clientes_map.get(c.get("cliente_id"), "")
        return ok(serialize_docs(cuentas))

    def post(self, request):
        data = request.data
        for campo in ("nombre", "cliente_id"):
            if not data.get(campo):
                return bad_request(f"'{campo}' es requerido.")

        cliente_oid = to_oid(data["cliente_id"])
        if not cliente_oid:
            return bad_request("'cliente_id' inválido.")

        db = get_db()
        if not db.clientes.find_one({"_id": cliente_oid}):
            return not_found("Cliente no encontrado.")

        numero = data.get("numero", "").strip()
        if numero and db.cuentas.find_one({"cliente_id": cliente_oid, "numero": numero}):
            return bad_request("Ya existe una cuenta con ese número para este cliente.")

        doc = {
            "cliente_id": cliente_oid,
            "nombre": data["nombre"].strip(),
            "numero": numero,
            "direccion": data.get("direccion", "").strip(),
            "distrito": data.get("distrito", "").strip(),
            "contacto": data.get("contacto", "").strip(),
            "telefono": data.get("telefono", "").strip(),
            "tipo": data.get("tipo", "empresa"),
            "latitud": float(data.get("latitud", 0) or 0),
            "longitud": float(data.get("longitud", 0) or 0),
            "activa": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        result = db.cuentas.insert_one(doc)
        doc["_id"] = result.inserted_id
        return created(serialize_doc(doc))


class CuentaDetailView(APIView):
    permission_classes = [EsCoordinadorOAdmin]

    def get(self, request, pk):
        try:
            oid = require_oid(pk)
        except ValueError as e:
            return bad_request(str(e))
        c = get_db().cuentas.find_one({"_id": oid})
        if not c:
            return not_found("Cuenta no encontrada.")
        return ok(serialize_doc(c))

    def put(self, request, pk):
        try:
            oid = require_oid(pk)
        except ValueError as e:
            return bad_request(str(e))

        db = get_db()
        if not db.cuentas.find_one({"_id": oid}):
            return not_found()

        update: dict = {"updated_at": datetime.now(timezone.utc)}
        for field in ("nombre", "numero", "direccion", "distrito", "contacto", "telefono", "tipo"):
            if field in request.data:
                update[field] = request.data[field]
        for field in ("latitud", "longitud"):
            if field in request.data:
                update[field] = float(request.data[field] or 0)
        if "activa" in request.data:
            update["activa"] = bool(request.data["activa"])

        db.cuentas.update_one({"_id": oid}, {"$set": update})
        return ok(serialize_doc(db.cuentas.find_one({"_id": oid})))

    def delete(self, request, pk):
        try:
            oid = require_oid(pk)
        except ValueError as e:
            return bad_request(str(e))

        db = get_db()
        if not db.cuentas.find_one({"_id": oid}):
            return not_found()
        db.cuentas.update_one({"_id": oid}, {"$set": {"activa": False}})
        return no_content()

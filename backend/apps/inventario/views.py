from __future__ import annotations

import re
from datetime import datetime, timezone

from rest_framework.views import APIView

from apps.core.db import get_db
from apps.core.helpers import (
    bad_request, created, no_content, not_found, ok,
    require_oid, serialize_doc, serialize_docs,
)
from apps.core.permissions import EsCoordinadorOAdmin

CATEGORIAS_VALIDAS = ("material", "epp", "herramienta", "otro")


class InventarioListView(APIView):
    permission_classes = [EsCoordinadorOAdmin]

    def get(self, request):
        db = get_db()
        filtro: dict = {}
        activo_param = request.query_params.get("activo", "true").lower()
        if activo_param != "all":
            filtro["activo"] = activo_param != "false"
        if "categoria" in request.query_params:
            filtro["categoria"] = request.query_params["categoria"]
        q = request.query_params.get("q", "").strip()
        if q:
            regex = re.compile(re.escape(q), re.IGNORECASE)
            filtro["$or"] = [{"sku": regex}, {"nombre": regex}, {"descripcion": regex}]

        items = list(db.inventario.find(filtro).sort("nombre", 1))
        return ok(serialize_docs(items))

    def post(self, request):
        data = request.data
        for campo in ("sku", "nombre"):
            if not data.get(campo):
                return bad_request(f"'{campo}' es requerido.")

        db = get_db()
        if db.inventario.find_one({"sku": data["sku"].strip()}):
            return bad_request("Ya existe un ítem con ese SKU.")

        doc = {
            "sku": data["sku"].strip().upper(),
            "nombre": data["nombre"].strip(),
            "descripcion": data.get("descripcion", "").strip(),
            "categoria": data.get("categoria", "material"),
            "unidad": data.get("unidad", "unidad"),
            "precio_unitario": float(data.get("precio_unitario", 0) or 0),
            "stock_disponible": int(data.get("stock_disponible", 0) or 0),
            "stock_minimo": int(data.get("stock_minimo", 0) or 0),
            "activo": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        result = db.inventario.insert_one(doc)
        doc["_id"] = result.inserted_id
        return created(serialize_doc(doc))


class InventarioDetailView(APIView):
    permission_classes = [EsCoordinadorOAdmin]

    def get(self, request, pk):
        try:
            oid = require_oid(pk)
        except ValueError as e:
            return bad_request(str(e))
        item = get_db().inventario.find_one({"_id": oid})
        if not item:
            return not_found("Ítem no encontrado.")
        return ok(serialize_doc(item))

    def put(self, request, pk):
        try:
            oid = require_oid(pk)
        except ValueError as e:
            return bad_request(str(e))

        db = get_db()
        if not db.inventario.find_one({"_id": oid}):
            return not_found()

        update: dict = {"updated_at": datetime.now(timezone.utc)}
        for field in ("nombre", "descripcion", "categoria", "unidad"):
            if field in request.data:
                update[field] = request.data[field]
        for field in ("precio_unitario",):
            if field in request.data:
                update[field] = float(request.data[field] or 0)
        for field in ("stock_disponible", "stock_minimo"):
            if field in request.data:
                update[field] = int(request.data[field] or 0)
        if "activo" in request.data:
            update["activo"] = bool(request.data["activo"])

        db.inventario.update_one({"_id": oid}, {"$set": update})
        updated = db.inventario.find_one({"_id": oid})

        # Alerta de stock bajo
        if updated and updated.get("stock_disponible", 0) <= updated.get("stock_minimo", 0):
            _crear_alerta_stock(db, updated)

        return ok(serialize_doc(updated))

    def delete(self, request, pk):
        try:
            oid = require_oid(pk)
        except ValueError as e:
            return bad_request(str(e))

        db = get_db()
        if not db.inventario.find_one({"_id": oid}):
            return not_found()
        db.inventario.update_one({"_id": oid}, {"$set": {"activo": False}})
        return no_content()


def _crear_alerta_stock(db, item: dict) -> None:
    from apps.notificaciones.services import crear_notificacion
    crear_notificacion(
        db=db,
        tipo="stock_bajo",
        titulo="Stock bajo",
        mensaje=f"El ítem '{item['nombre']}' tiene stock bajo ({item['stock_disponible']} {item.get('unidad', 'unidades')}).",
        para_rol="coordinador",
        pedido_id=None,
    )

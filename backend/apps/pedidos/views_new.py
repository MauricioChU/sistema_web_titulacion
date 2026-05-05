from __future__ import annotations

import os
import re
from datetime import datetime, timezone

from django.conf import settings
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.db import get_db
from apps.core.helpers import (
    bad_request, created, no_content, not_found, ok,
    require_oid, serialize_doc, serialize_docs, to_oid,
)
from apps.core.permissions import EsCoordinadorOAdmin, EsTecnicoOAdmin

from . import services


def _get_pedido(pk: str):
    try:
        oid = require_oid(pk)
    except ValueError:
        return None, None
    db = get_db()
    pedido = db.pedidos.find_one({"_id": oid})
    return db, pedido


def _get_tecnico_doc(db, user: dict):
    return db.tecnicos.find_one({"user_id": user["_id"]})


class PedidoListView(APIView):
    """GET  /api/pedidos/  → listar pedidos
       POST /api/pedidos/  → crear pedido (coordinador/admin)"""

    def get_permissions(self):
        if self.request.method == "POST":
            return [EsCoordinadorOAdmin()]
        return [IsAuthenticated()]

    def get(self, request):
        db = get_db()
        user = request.user
        rol = user.get("rol", "")

        filtro: dict = {}

        # Técnicos solo ven sus pedidos asignados
        if rol == "tecnico":
            tecnico_doc = _get_tecnico_doc(db, user)
            if not tecnico_doc:
                return ok([])
            filtro["tecnico_asignado_id"] = tecnico_doc["_id"]

        # Filtros opcionales
        if "fase" in request.query_params:
            filtro["fase"] = request.query_params["fase"]
        if "estado" in request.query_params:
            filtro["estado"] = request.query_params["estado"]
        if "prioridad" in request.query_params:
            filtro["prioridad"] = request.query_params["prioridad"]
        if "tecnico_id" in request.query_params:
            t_oid = to_oid(request.query_params["tecnico_id"])
            if t_oid:
                filtro["tecnico_asignado_id"] = t_oid

        # Búsqueda por texto
        q = request.query_params.get("q", "").strip()
        if q:
            regex = re.compile(re.escape(q), re.IGNORECASE)
            filtro["$or"] = [
                {"codigo": regex}, {"titulo": regex},
                {"cliente_nombre": regex}, {"zona": regex},
            ]

        # Por defecto excluir dados de baja, salvo que se pida explícitamente
        if "estado" not in filtro and request.query_params.get("include_bajas", "false").lower() != "true":
            filtro["estado"] = {"$ne": "dado-de-baja"}

        pedidos = list(db.pedidos.find(filtro).sort("created_at", -1))
        return ok(serialize_docs(pedidos))

    def post(self, request):
        data = request.data
        for campo in ("titulo", "cliente_id"):
            if not data.get(campo):
                return bad_request(f"'{campo}' es requerido.")

        db = get_db()
        if data.get("cliente_id") and not db.clientes.find_one({"_id": to_oid(data["cliente_id"])}):
            return not_found("Cliente no encontrado.")

        pedido = services.crear_pedido(db, data, request.user.get("username", "sistema"))
        return created(serialize_doc(pedido))


class PedidoDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ("PUT", "DELETE"):
            return [EsCoordinadorOAdmin()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        db, pedido = _get_pedido(pk)
        if not pedido:
            return not_found("Pedido no encontrado.")
        return ok(serialize_doc(pedido))

    def put(self, request, pk):
        db, pedido = _get_pedido(pk)
        if not pedido:
            return not_found()

        update: dict = {"updated_at": datetime.now(timezone.utc)}
        for field in ("titulo", "descripcion", "tipo_servicio", "zona", "prioridad"):
            if field in request.data:
                update[field] = request.data[field]
        if "fecha_programada" in request.data:
            try:
                update["fecha_programada"] = datetime.fromisoformat(
                    request.data["fecha_programada"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

        db.pedidos.update_one({"_id": pedido["_id"]}, {"$set": update})
        return ok(serialize_doc(db.pedidos.find_one({"_id": pedido["_id"]})))

    def delete(self, request, pk):
        db, pedido = _get_pedido(pk)
        if not pedido:
            return not_found()
        db.pedidos.delete_one({"_id": pedido["_id"]})
        return no_content()


# --------------------------------------------------------------------------- #
# Acciones de coordinador                                                     #
# --------------------------------------------------------------------------- #

class PedidoAsignarView(APIView):
    """POST /api/pedidos/{id}/asignar/"""
    permission_classes = [EsCoordinadorOAdmin]

    def post(self, request, pk):
        db, pedido = _get_pedido(pk)
        if not pedido:
            return not_found()
        if not request.data.get("tecnico_id"):
            return bad_request("'tecnico_id' es requerido.")

        try:
            actualizado = services.asignar_tecnico(
                db=db,
                pedido=pedido,
                tecnico_id=request.data["tecnico_id"],
                epps=request.data.get("epps", []),
                materiales_req=request.data.get("materiales_requeridos", []),
                usuario=request.user.get("username", "sistema"),
            )
        except ValueError as e:
            return bad_request(str(e))

        return ok(serialize_doc(actualizado))


class PedidoReasignarView(APIView):
    """POST /api/pedidos/{id}/reasignar/ — tras rechazo"""
    permission_classes = [EsCoordinadorOAdmin]

    def post(self, request, pk):
        db, pedido = _get_pedido(pk)
        if not pedido:
            return not_found()
        if pedido.get("estado") != "rechazado":
            return bad_request("El pedido no está en estado 'rechazado'.")
        if not request.data.get("tecnico_id"):
            return bad_request("'tecnico_id' es requerido.")

        try:
            actualizado = services.reasignar_tecnico(
                db=db, pedido=pedido,
                nuevo_tecnico_id=request.data["tecnico_id"],
                usuario=request.user.get("username", "sistema"),
            )
        except ValueError as e:
            return bad_request(str(e))
        return ok(serialize_doc(actualizado))


class PedidoCompletarView(APIView):
    """POST /api/pedidos/{id}/completar/"""
    permission_classes = [EsCoordinadorOAdmin]

    def post(self, request, pk):
        db, pedido = _get_pedido(pk)
        if not pedido:
            return not_found()
        if pedido.get("estado") not in ("cierre-tecnico",):
            return bad_request("El pedido debe estar en estado 'cierre-tecnico' para completarlo.")
        actualizado = services.completar_pedido(db, pedido, request.user.get("username", "sistema"))
        return ok(serialize_doc(actualizado))


class PedidoDarDeBajaView(APIView):
    """POST /api/pedidos/{id}/dar-de-baja/"""
    permission_classes = [EsCoordinadorOAdmin]

    def post(self, request, pk):
        db, pedido = _get_pedido(pk)
        if not pedido:
            return not_found()
        motivo = request.data.get("motivo", "").strip()
        if not motivo:
            return bad_request("'motivo' es requerido.")
        actualizado = services.dar_de_baja(db, pedido, motivo, request.user.get("username", "sistema"))
        return ok(serialize_doc(actualizado))


# --------------------------------------------------------------------------- #
# Acciones de técnico                                                         #
# --------------------------------------------------------------------------- #

class PedidoConfirmarView(APIView):
    """POST /api/pedidos/{id}/confirmar/"""
    permission_classes = [EsTecnicoOAdmin]

    def post(self, request, pk):
        db, pedido = _get_pedido(pk)
        if not pedido:
            return not_found()
        if pedido.get("estado") not in ("por-confirmar",):
            return bad_request("El pedido no está pendiente de confirmación.")
        actualizado = services.confirmar_pedido(db, pedido, request.user.get("username", "sistema"))
        return ok(serialize_doc(actualizado))


class PedidoRechazarView(APIView):
    """POST /api/pedidos/{id}/rechazar/"""
    permission_classes = [EsTecnicoOAdmin]

    def post(self, request, pk):
        db, pedido = _get_pedido(pk)
        if not pedido:
            return not_found()
        if pedido.get("estado") not in ("por-confirmar",):
            return bad_request("Solo se puede rechazar un pedido en estado 'por-confirmar'.")
        motivo = request.data.get("motivo", "").strip()
        if not motivo:
            return bad_request("'motivo' es requerido para rechazar un pedido.")

        tecnico_doc = _get_tecnico_doc(db, request.user)
        tecnico_nombre = tecnico_doc["nombre"] if tecnico_doc else request.user.get("username", "técnico")
        actualizado = services.rechazar_pedido(
            db, pedido, motivo, tecnico_nombre, request.user.get("username", "sistema")
        )
        return ok(serialize_doc(actualizado))


class PedidoChecklistView(APIView):
    """POST /api/pedidos/{id}/checklist/"""
    permission_classes = [EsTecnicoOAdmin]

    def post(self, request, pk):
        db, pedido = _get_pedido(pk)
        if not pedido:
            return not_found()
        step_id = request.data.get("step_id", "").strip()
        if not step_id:
            return bad_request("'step_id' es requerido.")
        try:
            actualizado = services.actualizar_checklist(
                db=db, pedido=pedido,
                step_id=step_id,
                completado=bool(request.data.get("completado", False)),
                nota=request.data.get("nota", ""),
                usuario=request.user.get("username", "sistema"),
            )
        except ValueError as e:
            return bad_request(str(e))
        return ok(serialize_doc(actualizado))


class PedidoEvidenciaView(APIView):
    """POST /api/pedidos/{id}/evidencia/"""
    permission_classes = [EsTecnicoOAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        db, pedido = _get_pedido(pk)
        if not pedido:
            return not_found()

        archivo = request.FILES.get("archivo")
        if not archivo:
            return bad_request("'archivo' es requerido.")

        stage = request.data.get("stage", "antes")
        if stage not in ("antes", "despues"):
            return bad_request("'stage' debe ser 'antes' o 'despues'.")

        # Guardar archivo en media/evidencias/{codigo}/
        codigo = pedido.get("codigo", "sin-codigo")
        carpeta = os.path.join(settings.MEDIA_ROOT, "evidencias", codigo, stage)
        os.makedirs(carpeta, exist_ok=True)

        nombre_archivo = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{archivo.name}"
        ruta_completa = os.path.join(carpeta, nombre_archivo)
        with open(ruta_completa, "wb") as f:
            for chunk in archivo.chunks():
                f.write(chunk)

        ruta_relativa = f"evidencias/{codigo}/{stage}/{nombre_archivo}"

        actualizado = services.registrar_evidencia(
            db=db, pedido=pedido,
            archivo_path=ruta_relativa,
            nombre=archivo.name,
            descripcion=request.data.get("descripcion", ""),
            stage=stage,
            usuario=request.user.get("username", "sistema"),
        )
        return ok(serialize_doc(actualizado))


class PedidoDiagnosticoView(APIView):
    """PATCH /api/pedidos/{id}/diagnostico/"""
    permission_classes = [EsTecnicoOAdmin]

    def patch(self, request, pk):
        db, pedido = _get_pedido(pk)
        if not pedido:
            return not_found()
        texto = request.data.get("diagnostico_tecnico", "").strip()
        if not texto:
            return bad_request("'diagnostico_tecnico' es requerido.")
        actualizado = services.actualizar_diagnostico(db, pedido, texto, request.user.get("username", "sistema"))
        return ok(serialize_doc(actualizado))


class PedidoMaterialesView(APIView):
    """POST /api/pedidos/{id}/materiales/"""
    permission_classes = [EsTecnicoOAdmin]

    def post(self, request, pk):
        db, pedido = _get_pedido(pk)
        if not pedido:
            return not_found()
        materiales = request.data.get("materiales", [])
        if not isinstance(materiales, list):
            return bad_request("'materiales' debe ser una lista.")
        actualizado = services.registrar_materiales_usados(
            db, pedido, materiales, request.user.get("username", "sistema")
        )
        return ok(serialize_doc(actualizado))


class PedidoInformeView(APIView):
    """POST /api/pedidos/{id}/informe/"""
    permission_classes = [EsTecnicoOAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        db, pedido = _get_pedido(pk)
        if not pedido:
            return not_found()

        firma = request.FILES.get("firma_cliente")
        firma_path = None
        if firma:
            codigo = pedido.get("codigo", "sin-codigo")
            carpeta = os.path.join(settings.MEDIA_ROOT, "firmas", codigo)
            os.makedirs(carpeta, exist_ok=True)
            nombre = f"firma_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{firma.name}"
            ruta = os.path.join(carpeta, nombre)
            with open(ruta, "wb") as f:
                for chunk in firma.chunks():
                    f.write(chunk)
            firma_path = f"firmas/{codigo}/{nombre}"

        actualizado = services.cerrar_con_informe(
            db=db, pedido=pedido,
            data=request.data,
            firma_path=firma_path,
            usuario=request.user.get("username", "sistema"),
        )
        return ok(serialize_doc(actualizado))

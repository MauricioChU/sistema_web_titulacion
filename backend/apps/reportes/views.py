from __future__ import annotations

import os

from django.conf import settings
from django.http import FileResponse, HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.db import get_db
from apps.core.helpers import bad_request, not_found, require_oid

from .pdf_generator import generar_pdf_pedido


class ReportePedidoView(APIView):
    """GET /api/reportes/pedido/{id}/pdf/ → genera y devuelve el PDF"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            oid = require_oid(pk)
        except ValueError as e:
            return bad_request(str(e))

        db = get_db()
        pedido = db.pedidos.find_one({"_id": oid})
        if not pedido:
            return not_found("Pedido no encontrado.")

        try:
            pdf_bytes = generar_pdf_pedido(pedido)
        except Exception as exc:
            return bad_request(f"Error al generar PDF: {exc}")

        codigo = pedido.get("codigo", str(pk))
        carpeta = os.path.join(settings.MEDIA_ROOT, "reportes")
        os.makedirs(carpeta, exist_ok=True)
        ruta_pdf = os.path.join(carpeta, f"{codigo}.pdf")
        with open(ruta_pdf, "wb") as f:
            f.write(pdf_bytes)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="reporte_{codigo}.pdf"'
        return response

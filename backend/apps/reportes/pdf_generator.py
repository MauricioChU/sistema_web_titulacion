from __future__ import annotations

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

# Paleta de colores
AZUL = colors.HexColor("#1e40af")
AZUL_CLARO = colors.HexColor("#dbeafe")
GRIS = colors.HexColor("#6b7280")
GRIS_CLARO = colors.HexColor("#f3f4f6")
ROJO = colors.HexColor("#dc2626")
VERDE = colors.HexColor("#16a34a")
NARANJA = colors.HexColor("#d97706")
MORADO = colors.HexColor("#7c3aed")


def _color_prioridad(prioridad: str):
    return {
        "critica": ROJO,
        "alta": NARANJA,
        "media": AZUL,
        "baja": VERDE,
    }.get(prioridad, GRIS)


def _color_estado(estado: str):
    return {
        "completado": VERDE,
        "en-labor": AZUL,
        "confirmado": MORADO,
        "por-confirmar": NARANJA,
        "rechazado": ROJO,
        "dado-de-baja": GRIS,
    }.get(estado, GRIS)


def _fmt_dt(val) -> str:
    if not val:
        return "—"
    if isinstance(val, datetime):
        return val.strftime("%d/%m/%Y %H:%M")
    return str(val)


def generar_pdf_pedido(pedido: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story = []

    # ---- Estilos personalizados ----
    titulo_style = ParagraphStyle("Titulo", parent=styles["Heading1"], fontSize=20,
                                   textColor=AZUL, spaceAfter=4)
    subtitulo_style = ParagraphStyle("Subtitulo", parent=styles["Heading2"], fontSize=13,
                                      textColor=AZUL, spaceBefore=12, spaceAfter=6,
                                      borderPad=4)
    normal = styles["Normal"]
    small = ParagraphStyle("Small", parent=normal, fontSize=9, textColor=GRIS)
    bold = ParagraphStyle("Bold", parent=normal, fontName="Helvetica-Bold")

    # ---- Encabezado ----
    story.append(Paragraph("PROINTEL", ParagraphStyle("Brand", parent=normal, fontSize=11,
                                                        textColor=GRIS, fontName="Helvetica-Bold")))
    story.append(Paragraph(f"Reporte de Pedido · {pedido.get('codigo', 'SIN CÓDIGO')}", titulo_style))
    story.append(Paragraph(
        f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        small,
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=AZUL, spaceAfter=12))

    # ---- Info general ----
    story.append(Paragraph("Información General", subtitulo_style))
    prioridad = pedido.get("prioridad", "—")
    estado = pedido.get("estado", "—")

    datos_gen = [
        ["Código", pedido.get("codigo", "—"), "Prioridad", prioridad.upper()],
        ["Cliente", pedido.get("cliente_nombre", "—"), "Estado", estado.upper()],
        ["Cuenta/Sede", pedido.get("cuenta_nombre", "—"), "Zona", pedido.get("zona", "—")],
        ["Tipo de servicio", pedido.get("tipo_servicio", "—"), "Técnico asignado", pedido.get("tecnico_nombre") or "Sin asignar"],
        ["Fecha programada", _fmt_dt(pedido.get("fecha_programada")), "Fecha de cierre", _fmt_dt(pedido.get("fecha_cierre"))],
        ["Creado el", _fmt_dt(pedido.get("created_at")), "Inicio labor", _fmt_dt(pedido.get("fecha_inicio_labor"))],
    ]
    t = Table(datos_gen, colWidths=[4 * cm, 6.5 * cm, 4 * cm, 6.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), GRIS_CLARO),
        ("BACKGROUND", (2, 0), (2, -1), GRIS_CLARO),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.3 * cm))

    # Título y descripción
    story.append(Paragraph("Descripción del Pedido", subtitulo_style))
    story.append(Paragraph(f"<b>Título:</b> {pedido.get('titulo', '—')}", normal))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(pedido.get("descripcion", "Sin descripción."), normal))

    # ---- Checklist ----
    checklist = pedido.get("checklist", [])
    if checklist:
        story.append(Paragraph("Checklist de Ejecución", subtitulo_style))
        chk_data = [["Paso", "Estado", "Nota", "Completado"]]
        for step in checklist:
            estado_chk = "✓ Completado" if step.get("completado") else "○ Pendiente"
            chk_data.append([
                step.get("label", step.get("step_id", "")),
                estado_chk,
                step.get("nota", "—") or "—",
                _fmt_dt(step.get("completado_en")),
            ])
        tc = Table(chk_data, colWidths=[5 * cm, 3.5 * cm, 5.5 * cm, 4.5 * cm])
        tc.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(tc)

    # ---- EPPs asignados ----
    epps = pedido.get("epps_asignados", [])
    if epps:
        story.append(Paragraph("EPPs Asignados", subtitulo_style))
        epp_data = [["SKU", "Nombre", "Cantidad", "Precio Unit.", "Subtotal"]]
        for e in epps:
            subtotal = float(e.get("precio_unitario", 0)) * int(e.get("cantidad", 0))
            epp_data.append([
                e.get("sku", "—"),
                e.get("nombre", "—"),
                str(e.get("cantidad", 0)),
                f"S/ {e.get('precio_unitario', 0):.2f}",
                f"S/ {subtotal:.2f}",
            ])
        te = Table(epp_data, colWidths=[3 * cm, 6 * cm, 2.5 * cm, 3.5 * cm, 3.5 * cm])
        te.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NARANJA),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(te)

    # ---- Materiales usados ----
    materiales = pedido.get("materiales_usados", [])
    if materiales:
        story.append(Paragraph("Materiales Utilizados", subtitulo_style))
        mat_data = [["SKU", "Nombre", "Cantidad", "Precio Unit.", "Subtotal"]]
        for m in materiales:
            subtotal = float(m.get("precio_unitario", 0)) * int(m.get("cantidad", 0))
            mat_data.append([
                m.get("sku", "—"),
                m.get("nombre", "—"),
                str(m.get("cantidad", 0)),
                f"S/ {m.get('precio_unitario', 0):.2f}",
                f"S/ {subtotal:.2f}",
            ])
        tm = Table(mat_data, colWidths=[3 * cm, 6 * cm, 2.5 * cm, 3.5 * cm, 3.5 * cm])
        tm.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), VERDE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(tm)

    # ---- Resumen de costos ----
    story.append(Paragraph("Resumen de Costos", subtitulo_style))
    costo_epps = pedido.get("costo_epps", 0)
    costo_mat = pedido.get("costo_materiales", 0)
    costo_total = pedido.get("costo_total", 0)
    costos_data = [
        ["Concepto", "Monto"],
        ["EPPs asignados", f"S/ {costo_epps:.2f}"],
        ["Materiales utilizados", f"S/ {costo_mat:.2f}"],
        ["TOTAL", f"S/ {costo_total:.2f}"],
    ]
    tcosto = Table(costos_data, colWidths=[10 * cm, 4 * cm])
    tcosto.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), AZUL_CLARO),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(tcosto)

    # ---- Diagnóstico ----
    diag = pedido.get("diagnostico_tecnico", "").strip()
    if diag:
        story.append(Paragraph("Diagnóstico Técnico", subtitulo_style))
        story.append(Paragraph(diag, normal))

    # ---- Evidencias ----
    evidencias = pedido.get("evidencias", [])
    if evidencias:
        story.append(Paragraph(f"Evidencias ({len(evidencias)})", subtitulo_style))
        ev_data = [["Nombre", "Tipo", "Subida por", "Fecha"]]
        for ev in evidencias:
            ev_data.append([
                ev.get("nombre", "—"),
                ev.get("stage", "—").upper(),
                ev.get("subida_por", "—"),
                _fmt_dt(ev.get("uploaded_at")),
            ])
        tev = Table(ev_data, colWidths=[6 * cm, 2.5 * cm, 4 * cm, 4.5 * cm])
        tev.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), MORADO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(tev)

    # ---- Informe técnico ----
    informe = pedido.get("informe")
    if informe:
        story.append(Paragraph("Informe Técnico Final", subtitulo_style))
        campos_informe = [
            ("Diagnóstico final", informe.get("diagnostico_final", "—")),
            ("Responsable local", informe.get("responsable_local", "—")),
            ("Servicio solicitado", informe.get("pedido_solicitado", "—")),
            ("Observaciones", informe.get("observaciones", "—")),
            ("Recomendaciones", informe.get("recomendaciones", "—")),
        ]
        for label, value in campos_informe:
            story.append(Paragraph(f"<b>{label}:</b> {value}", normal))
            story.append(Spacer(1, 0.15 * cm))

    # ---- Historial ----
    historial = pedido.get("historial", [])
    if historial:
        story.append(Paragraph("Historial de Eventos", subtitulo_style))
        hist_data = [["Evento", "Detalle", "Usuario", "Fecha"]]
        for h in historial[-20:]:  # Últimos 20 eventos
            hist_data.append([
                h.get("evento", "—"),
                Paragraph(h.get("detalle", "—"), ParagraphStyle("tiny", fontSize=8)),
                h.get("usuario", "—"),
                _fmt_dt(h.get("at")),
            ])
        th = Table(hist_data, colWidths=[3.5 * cm, 7 * cm, 3 * cm, 4 * cm])
        th.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), GRIS),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(th)

    # ---- Pie ----
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=GRIS))
    story.append(Paragraph(
        f"PROINTEL Sistema de Gestión · {datetime.now().strftime('%d/%m/%Y')}",
        ParagraphStyle("footer", parent=small, alignment=1),
    ))

    doc.build(story)
    return buf.getvalue()

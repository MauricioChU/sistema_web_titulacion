from __future__ import annotations

from datetime import datetime, timezone
from bson import ObjectId
from pymongo.database import Database


# --------------------------------------------------------------------------- #
# Constantes del estado de pedidos                                            #
# --------------------------------------------------------------------------- #

FASES = ("creacion", "programacion", "seguimiento", "cierre")
ESTADOS = (
    "por-confirmar", "confirmado", "rechazado", "en-labor",
    "cierre-tecnico", "completado", "dado-de-baja",
)

CHECKLIST_STEPS = [
    {"step_id": "materiales-listos", "label": "Materiales listos"},
    {"step_id": "llegada-sitio",     "label": "Llegada al sitio"},
    {"step_id": "inicio-trabajo",    "label": "Inicio de trabajo"},
    {"step_id": "nota-adicional",    "label": "Nota adicional"},
]


# --------------------------------------------------------------------------- #
# Helpers internos                                                             #
# --------------------------------------------------------------------------- #

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _historial_entry(evento: str, detalle: str, usuario: str) -> dict:
    return {"evento": evento, "detalle": detalle, "usuario": usuario, "at": _now()}


def _recalcular_costos(pedido: dict) -> dict:
    costo_epps = sum(
        float(e.get("precio_unitario", 0)) * int(e.get("cantidad", 0))
        for e in pedido.get("epps_asignados", [])
    )
    costo_materiales = sum(
        float(m.get("precio_unitario", 0)) * int(m.get("cantidad", 0))
        for m in pedido.get("materiales_usados", [])
    )
    return {
        "costo_epps": round(costo_epps, 2),
        "costo_materiales": round(costo_materiales, 2),
        "costo_total": round(costo_epps + costo_materiales, 2),
    }


def _siguiente_codigo(db: Database) -> str:
    ultimo = db.pedidos.find_one({}, sort=[("codigo", -1)])
    if not ultimo or not ultimo.get("codigo"):
        return "P0001"
    num_str = ultimo["codigo"].lstrip("P")
    try:
        num = int(num_str) + 1
    except ValueError:
        num = 1
    return f"P{num:04d}"


# --------------------------------------------------------------------------- #
# Crear pedido                                                                #
# --------------------------------------------------------------------------- #

def crear_pedido(db: Database, data: dict, usuario: str) -> dict:
    from apps.core.helpers import to_oid

    cliente_oid = to_oid(data.get("cliente_id"))
    cuenta_oid = to_oid(data.get("cuenta_id"))

    cliente = db.clientes.find_one({"_id": cliente_oid}) if cliente_oid else None
    cuenta = db.cuentas.find_one({"_id": cuenta_oid}) if cuenta_oid else None

    doc = {
        "codigo": _siguiente_codigo(db),
        "cliente_id": cliente_oid,
        "cuenta_id": cuenta_oid,
        "cliente_nombre": cliente["nombre"] if cliente else "",
        "cuenta_nombre": cuenta["nombre"] if cuenta else "",
        "titulo": data.get("titulo", "").strip(),
        "descripcion": data.get("descripcion", "").strip(),
        "tipo_servicio": data.get("tipo_servicio", "").strip(),
        "zona": data.get("zona", "").strip(),
        "prioridad": data.get("prioridad", "media"),
        "fase": "creacion",
        "estado": "por-confirmar",
        "tecnico_asignado_id": None,
        "tecnico_nombre": None,
        "epps_asignados": [],
        "materiales_requeridos": [],
        "checklist": [
            {**step, "completado": False, "nota": "", "completado_en": None}
            for step in CHECKLIST_STEPS
        ],
        "evidencias": [],
        "diagnostico_tecnico": "",
        "materiales_usados": [],
        "costo_epps": 0.0,
        "costo_materiales": 0.0,
        "costo_total": 0.0,
        "informe": None,
        "motivo_rechazo": None,
        "historial_rechazos": [],
        "fecha_programada": None,
        "fecha_inicio_labor": None,
        "fecha_fin_labor": None,
        "fecha_cierre": None,
        "created_at": _now(),
        "updated_at": _now(),
        "historial": [_historial_entry("creacion", f"Pedido creado por {usuario}", usuario)],
    }

    result = db.pedidos.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


# --------------------------------------------------------------------------- #
# Asignar técnico + EPPs                                                      #
# --------------------------------------------------------------------------- #

def asignar_tecnico(db: Database, pedido: dict, tecnico_id: str, epps: list, materiales_req: list, usuario: str) -> dict:
    from apps.core.helpers import to_oid

    tecnico_oid = to_oid(tecnico_id)
    tecnico = db.tecnicos.find_one({"_id": tecnico_oid})
    if not tecnico:
        raise ValueError("Técnico no encontrado.")

    epps_enriquecidos = []
    for epp in epps:
        item_oid = to_oid(epp.get("item_id"))
        item = db.inventario.find_one({"_id": item_oid})
        if not item:
            continue
        epps_enriquecidos.append({
            "item_id": item_oid,
            "sku": item["sku"],
            "nombre": item["nombre"],
            "cantidad": int(epp.get("cantidad", 1)),
            "precio_unitario": float(item.get("precio_unitario", 0)),
        })

    mats_enriquecidos = []
    for mat in materiales_req:
        item_oid = to_oid(mat.get("item_id"))
        item = db.inventario.find_one({"_id": item_oid})
        if not item:
            continue
        mats_enriquecidos.append({
            "item_id": item_oid,
            "sku": item["sku"],
            "nombre": item["nombre"],
            "cantidad": int(mat.get("cantidad", 1)),
            "precio_unitario": float(item.get("precio_unitario", 0)),
        })

    update = {
        "tecnico_asignado_id": tecnico_oid,
        "tecnico_nombre": tecnico["nombre"],
        "epps_asignados": epps_enriquecidos,
        "materiales_requeridos": mats_enriquecidos,
        "estado": "por-confirmar",
        "fase": "creacion",
        "updated_at": _now(),
    }
    costos = _recalcular_costos({**pedido, **update})
    update.update(costos)

    entry = _historial_entry("asignacion", f"Técnico '{tecnico['nombre']}' asignado por {usuario}", usuario)
    db.pedidos.update_one({"_id": pedido["_id"]}, {"$set": update, "$push": {"historial": entry}})

    from apps.notificaciones.services import crear_notificacion
    user_tecnico = db.users.find_one({"_id": tecnico["user_id"]})
    crear_notificacion(
        db=db, tipo="pedido_por_confirmar", titulo="Nuevo pedido asignado",
        mensaje=f"Se te asignó el pedido {pedido['codigo']}: {pedido['titulo']}",
        para_user_id=user_tecnico["_id"] if user_tecnico else None,
        pedido_id=pedido["_id"],
    )
    return db.pedidos.find_one({"_id": pedido["_id"]})


# --------------------------------------------------------------------------- #
# Confirmar pedido (técnico acepta)                                           #
# --------------------------------------------------------------------------- #

def confirmar_pedido(db: Database, pedido: dict, usuario: str) -> dict:
    entry = _historial_entry("confirmacion", f"Pedido confirmado por técnico {usuario}", usuario)
    db.pedidos.update_one(
        {"_id": pedido["_id"]},
        {"$set": {"estado": "confirmado", "fase": "programacion", "updated_at": _now()}, "$push": {"historial": entry}},
    )
    return db.pedidos.find_one({"_id": pedido["_id"]})


# --------------------------------------------------------------------------- #
# Rechazar pedido (técnico rechaza)                                           #
# --------------------------------------------------------------------------- #

def rechazar_pedido(db: Database, pedido: dict, motivo: str, tecnico_nombre: str, usuario: str) -> dict:
    rechazo_entry = {"tecnico_nombre": tecnico_nombre, "motivo": motivo, "at": _now()}
    historial_entry = _historial_entry("rechazo", f"Rechazado por {tecnico_nombre}. Motivo: {motivo}", usuario)
    db.pedidos.update_one(
        {"_id": pedido["_id"]},
        {
            "$set": {"estado": "rechazado", "fase": "creacion", "motivo_rechazo": motivo, "updated_at": _now()},
            "$push": {"historial": historial_entry, "historial_rechazos": rechazo_entry},
        },
    )
    from apps.notificaciones.services import crear_notificacion
    msg = f"El técnico {tecnico_nombre} rechazó el pedido {pedido['codigo']}. Motivo: {motivo}"
    for rol in ("coordinador", "admin"):
        crear_notificacion(db=db, tipo="pedido_rechazado", titulo="Pedido rechazado", mensaje=msg,
                           para_rol=rol, pedido_id=pedido["_id"])
    return db.pedidos.find_one({"_id": pedido["_id"]})


# --------------------------------------------------------------------------- #
# Reasignar técnico tras rechazo                                              #
# --------------------------------------------------------------------------- #

def reasignar_tecnico(db: Database, pedido: dict, nuevo_tecnico_id: str, usuario: str) -> dict:
    from apps.core.helpers import to_oid
    tecnico_oid = to_oid(nuevo_tecnico_id)
    tecnico = db.tecnicos.find_one({"_id": tecnico_oid})
    if not tecnico:
        raise ValueError("Técnico no encontrado.")

    entry = _historial_entry("reasignacion", f"Reasignado a '{tecnico['nombre']}' por {usuario}", usuario)
    db.pedidos.update_one(
        {"_id": pedido["_id"]},
        {"$set": {"tecnico_asignado_id": tecnico_oid, "tecnico_nombre": tecnico["nombre"],
                  "estado": "por-confirmar", "motivo_rechazo": None, "updated_at": _now()},
         "$push": {"historial": entry}},
    )
    from apps.notificaciones.services import crear_notificacion
    user_tecnico = db.users.find_one({"_id": tecnico["user_id"]})
    crear_notificacion(db=db, tipo="pedido_por_confirmar", titulo="Pedido reasignado",
                       mensaje=f"Se te reasignó el pedido {pedido['codigo']}: {pedido['titulo']}",
                       para_user_id=user_tecnico["_id"] if user_tecnico else None, pedido_id=pedido["_id"])
    return db.pedidos.find_one({"_id": pedido["_id"]})


# --------------------------------------------------------------------------- #
# Checklist                                                                   #
# --------------------------------------------------------------------------- #

def actualizar_checklist(db: Database, pedido: dict, step_id: str, completado: bool, nota: str, usuario: str) -> dict:
    checklist = pedido.get("checklist", [])
    step_ids_validos = [s["step_id"] for s in CHECKLIST_STEPS]
    if step_id not in step_ids_validos:
        raise ValueError(f"step_id inválido. Opciones: {step_ids_validos}")

    for step in checklist:
        if step["step_id"] == step_id:
            step["completado"] = completado
            step["nota"] = nota
            step["completado_en"] = _now() if completado else None
            break

    update: dict = {"checklist": checklist, "updated_at": _now()}
    todos_completos = all(s["completado"] for s in checklist)
    if todos_completos and pedido.get("estado") != "en-labor":
        update["estado"] = "en-labor"
        update["fase"] = "seguimiento"
        update["fecha_inicio_labor"] = _now()

    entry = _historial_entry("checklist", f"Step '{step_id}' actualizado por {usuario}", usuario)
    db.pedidos.update_one({"_id": pedido["_id"]}, {"$set": update, "$push": {"historial": entry}})
    return db.pedidos.find_one({"_id": pedido["_id"]})


# --------------------------------------------------------------------------- #
# Evidencias                                                                  #
# --------------------------------------------------------------------------- #

def registrar_evidencia(db: Database, pedido: dict, archivo_path: str, nombre: str, descripcion: str, stage: str, usuario: str) -> dict:
    import uuid
    evidencia = {
        "id": str(uuid.uuid4()), "nombre": nombre, "archivo": archivo_path,
        "descripcion": descripcion, "stage": stage, "subida_por": usuario, "uploaded_at": _now(),
    }
    entry = _historial_entry("evidencia", f"Evidencia '{stage}' subida por {usuario}", usuario)
    db.pedidos.update_one(
        {"_id": pedido["_id"]},
        {"$push": {"evidencias": evidencia, "historial": entry}, "$set": {"updated_at": _now()}},
    )
    return db.pedidos.find_one({"_id": pedido["_id"]})


# --------------------------------------------------------------------------- #
# Diagnóstico técnico                                                         #
# --------------------------------------------------------------------------- #

def actualizar_diagnostico(db: Database, pedido: dict, texto: str, usuario: str) -> dict:
    entry = _historial_entry("diagnostico", f"Diagnóstico actualizado por {usuario}", usuario)
    db.pedidos.update_one(
        {"_id": pedido["_id"]},
        {"$set": {"diagnostico_tecnico": texto, "updated_at": _now()}, "$push": {"historial": entry}},
    )
    return db.pedidos.find_one({"_id": pedido["_id"]})


# --------------------------------------------------------------------------- #
# Materiales usados (descuenta stock)                                         #
# --------------------------------------------------------------------------- #

def registrar_materiales_usados(db: Database, pedido: dict, materiales: list, usuario: str) -> dict:
    from apps.core.helpers import to_oid
    materiales_docs = []
    for mat in materiales:
        item_oid = to_oid(mat.get("item_id"))
        item = db.inventario.find_one({"_id": item_oid})
        if not item:
            continue
        cantidad = int(mat.get("cantidad", 1))
        materiales_docs.append({
            "item_id": item_oid, "sku": item["sku"], "nombre": item["nombre"],
            "cantidad": cantidad, "precio_unitario": float(item.get("precio_unitario", 0)),
        })
        db.inventario.update_one({"_id": item_oid}, {"$inc": {"stock_disponible": -cantidad}})
        item_act = db.inventario.find_one({"_id": item_oid})
        if item_act and item_act.get("stock_disponible", 0) <= item_act.get("stock_minimo", 0):
            from apps.notificaciones.services import crear_notificacion
            crear_notificacion(db=db, tipo="stock_bajo", titulo="Stock bajo",
                               mensaje=f"Ítem '{item['nombre']}' con stock bajo ({item_act['stock_disponible']} {item.get('unidad','uds')}).",
                               para_rol="coordinador", pedido_id=pedido["_id"])

    costos = _recalcular_costos({**pedido, "materiales_usados": materiales_docs})
    entry = _historial_entry("materiales", f"Materiales usados registrados por {usuario}", usuario)
    db.pedidos.update_one(
        {"_id": pedido["_id"]},
        {"$set": {"materiales_usados": materiales_docs, **costos, "updated_at": _now()}, "$push": {"historial": entry}},
    )
    return db.pedidos.find_one({"_id": pedido["_id"]})


# --------------------------------------------------------------------------- #
# Informe técnico final                                                       #
# --------------------------------------------------------------------------- #

def cerrar_con_informe(db: Database, pedido: dict, data: dict, firma_path: str | None, usuario: str) -> dict:
    now = _now()
    informe = {
        "diagnostico_final": data.get("diagnostico_final", "").strip(),
        "responsable_local": data.get("responsable_local", "").strip(),
        "pedido_solicitado": data.get("pedido_solicitado", "").strip(),
        "observaciones": data.get("observaciones", "").strip(),
        "recomendaciones": data.get("recomendaciones", "").strip(),
        "firma_cliente": firma_path,
        "created_at": now,
    }
    entry = _historial_entry("informe", f"Informe técnico completado por {usuario}", usuario)
    db.pedidos.update_one(
        {"_id": pedido["_id"]},
        {"$set": {"informe": informe, "estado": "cierre-tecnico", "fase": "cierre",
                  "fecha_fin_labor": now, "updated_at": now},
         "$push": {"historial": entry}},
    )
    return db.pedidos.find_one({"_id": pedido["_id"]})


# --------------------------------------------------------------------------- #
# Completar / Dar de baja (coordinador)                                      #
# --------------------------------------------------------------------------- #

def completar_pedido(db: Database, pedido: dict, usuario: str) -> dict:
    now = _now()
    entry = _historial_entry("completado", f"Completado y cerrado por {usuario}", usuario)
    db.pedidos.update_one(
        {"_id": pedido["_id"]},
        {"$set": {"estado": "completado", "fase": "cierre", "fecha_cierre": now, "updated_at": now},
         "$push": {"historial": entry}},
    )
    from apps.notificaciones.services import crear_notificacion
    crear_notificacion(db=db, tipo="pedido_completado", titulo="Pedido completado",
                       mensaje=f"El pedido {pedido['codigo']} fue completado.", para_rol="todos",
                       pedido_id=pedido["_id"])
    return db.pedidos.find_one({"_id": pedido["_id"]})


def dar_de_baja(db: Database, pedido: dict, motivo: str, usuario: str) -> dict:
    entry = _historial_entry("baja", f"Dado de baja por {usuario}. Motivo: {motivo}", usuario)
    db.pedidos.update_one(
        {"_id": pedido["_id"]},
        {"$set": {"estado": "dado-de-baja", "motivo_rechazo": motivo, "updated_at": _now()},
         "$push": {"historial": entry}},
    )
    return db.pedidos.find_one({"_id": pedido["_id"]})

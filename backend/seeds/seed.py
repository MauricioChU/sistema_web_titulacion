"""
Seed de base de datos para PROINTEL.

Ejecutar desde el directorio backend/:
    python -m seeds.seed
    python -m seeds.seed --reset   (borra todo antes de insertar)
"""
from __future__ import annotations

import sys
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Asegurar que Django esté configurado
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

# Configurar stdout para UTF-8 en Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from django.contrib.auth.hashers import make_password
from bson import ObjectId
from apps.core.db import get_db, init_indexes

# ============================================================
# CONSTANTES / CUENTAS DE ACCESO
# ============================================================
print("=" * 55)
print("  PROINTEL - Seed de Base de Datos")
print("=" * 55)
print("  USUARIOS:")
print("  admin        / Admin2024!      (Admin)")
print("  coordinador1 / Coord2024!      (Coordinador)")
print("  coordinador2 / Coord2024!      (Coordinador Sup.)")
print("  tecnico1     / Tecnico2024!    (Tecnico)")
print("  tecnico2     / Tecnico2024!    (Tecnico)")
print("  tecnico3     / Tecnico2024!    (Tecnico)")
print("=" * 55)


def _now(offset_days: int = 0) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=offset_days)


def run(reset: bool = False):
    db = get_db()

    if reset:
        print("⚠  Limpiando colecciones...")
        for col in ("users", "tokens", "tecnicos", "clientes", "cuentas",
                    "inventario", "pedidos", "notificaciones"):
            db[col].drop()
        print("   Colecciones limpiadas.\n")

    init_indexes()

    # ================================================================
    # USUARIOS
    # ================================================================
    print("→ Creando usuarios...")
    PASS_ADMIN = make_password("Admin2024!")
    PASS_COORD = make_password("Coord2024!")
    PASS_TEC   = make_password("Tecnico2024!")

    admin_id = ObjectId()
    coord1_id = ObjectId()
    coord2_id = ObjectId()
    tec1_user_id = ObjectId()
    tec2_user_id = ObjectId()
    tec3_user_id = ObjectId()

    usuarios = [
        {
            "_id": admin_id,
            "username": "admin",
            "password_hash": PASS_ADMIN,
            "email": "admin@prointel.pe",
            "nombre_completo": "Administrador Principal",
            "rol": "admin",
            "privilegio": None,
            "activo": True,
            "created_at": _now(-30),
            "updated_at": _now(-30),
        },
        {
            "_id": coord1_id,
            "username": "coordinador1",
            "password_hash": PASS_COORD,
            "email": "coordinador1@prointel.pe",
            "nombre_completo": "Carlos Mendoza Torres",
            "rol": "coordinador",
            "privilegio": None,
            "activo": True,
            "created_at": _now(-25),
            "updated_at": _now(-25),
        },
        {
            "_id": coord2_id,
            "username": "coordinador2",
            "password_hash": PASS_COORD,
            "email": "coordinador2@prointel.pe",
            "nombre_completo": "Ana Quispe Rojas",
            "rol": "coordinador",
            "privilegio": "supervisor",
            "activo": True,
            "created_at": _now(-25),
            "updated_at": _now(-25),
        },
        {
            "_id": tec1_user_id,
            "username": "tecnico1",
            "password_hash": PASS_TEC,
            "email": "tecnico1@prointel.pe",
            "nombre_completo": "Pedro Huanca Flores",
            "rol": "tecnico",
            "privilegio": None,
            "activo": True,
            "created_at": _now(-20),
            "updated_at": _now(-20),
        },
        {
            "_id": tec2_user_id,
            "username": "tecnico2",
            "password_hash": PASS_TEC,
            "email": "tecnico2@prointel.pe",
            "nombre_completo": "Luis García Vega",
            "rol": "tecnico",
            "privilegio": None,
            "activo": True,
            "created_at": _now(-20),
            "updated_at": _now(-20),
        },
        {
            "_id": tec3_user_id,
            "username": "tecnico3",
            "password_hash": PASS_TEC,
            "email": "tecnico3@prointel.pe",
            "nombre_completo": "Rosa Mamani Condori",
            "rol": "tecnico",
            "privilegio": None,
            "activo": True,
            "created_at": _now(-20),
            "updated_at": _now(-20),
        },
    ]
    for u in usuarios:
        db.users.update_one({"username": u["username"]}, {"$setOnInsert": u}, upsert=True)
    print(f"   {len(usuarios)} usuarios OK.")

    # ================================================================
    # TÉCNICOS (perfiles)
    # ================================================================
    print("→ Creando perfiles de técnicos...")
    tec1_id = ObjectId()
    tec2_id = ObjectId()
    tec3_id = ObjectId()

    tecnicos = [
        {
            "_id": tec1_id,
            "user_id": tec1_user_id,
            "nombre": "Pedro Huanca Flores",
            "especialidad": "Redes y Cableado",
            "zona": "Lima Norte",
            "telefono": "987654321",
            "latitud_base": -11.9800,
            "longitud_base": -77.0560,
            "activo": True,
            "created_at": _now(-20),
        },
        {
            "_id": tec2_id,
            "user_id": tec2_user_id,
            "nombre": "Luis García Vega",
            "especialidad": "CCTV y Seguridad",
            "zona": "Lima Centro",
            "telefono": "976543210",
            "latitud_base": -12.0464,
            "longitud_base": -77.0428,
            "activo": True,
            "created_at": _now(-20),
        },
        {
            "_id": tec3_id,
            "user_id": tec3_user_id,
            "nombre": "Rosa Mamani Condori",
            "especialidad": "Control de Accesos",
            "zona": "Lima Sur",
            "telefono": "965432109",
            "latitud_base": -12.1500,
            "longitud_base": -76.9800,
            "activo": True,
            "created_at": _now(-20),
        },
    ]
    for t in tecnicos:
        db.tecnicos.update_one({"user_id": t["user_id"]}, {"$setOnInsert": t}, upsert=True)
        t_db = db.tecnicos.find_one({"user_id": t["user_id"]})
        if t["_id"] != t_db["_id"]:
            if t["_id"] == tec1_id: tec1_id = t_db["_id"]
            elif t["_id"] == tec2_id: tec2_id = t_db["_id"]
            elif t["_id"] == tec3_id: tec3_id = t_db["_id"]
    print(f"   {len(tecnicos)} técnicos OK.")

    # ================================================================
    # CLIENTES
    # ================================================================
    print("→ Creando clientes...")
    cli1_id = ObjectId()
    cli2_id = ObjectId()
    cli3_id = ObjectId()

    clientes = [
        {
            "_id": cli1_id,
            "nombre": "Liderman S.A.",
            "ruc": "20100179816",
            "telefono": "01-6122000",
            "correo": "operaciones@liderman.com.pe",
            "direccion": "Av. Javier Prado Este 4200, Lima",
            "activo": True,
            "created_at": _now(-60),
            "updated_at": _now(-60),
        },
        {
            "_id": cli2_id,
            "nombre": "BanBif S.A.",
            "ruc": "20101128937",
            "telefono": "01-6196000",
            "correo": "infraestructura@banbif.com.pe",
            "direccion": "Av. Rivera Navarrete 600, San Isidro",
            "activo": True,
            "created_at": _now(-60),
            "updated_at": _now(-60),
        },
        {
            "_id": cli3_id,
            "nombre": "Cineplanet S.A.",
            "ruc": "20508565934",
            "telefono": "01-6007000",
            "correo": "mantenimiento@cineplanet.com.pe",
            "direccion": "Av. Arequipa 3415, San Isidro",
            "activo": True,
            "created_at": _now(-60),
            "updated_at": _now(-60),
        },
    ]
    for c in clientes:
        db.clientes.update_one({"ruc": c["ruc"]}, {"$setOnInsert": c}, upsert=True)
    print(f"   {len(clientes)} clientes OK.")

    # ================================================================
    # CUENTAS / SEDES
    # ================================================================
    print("→ Creando cuentas/sedes...")
    cta1_id = ObjectId()
    cta2_id = ObjectId()
    cta3_id = ObjectId()
    cta4_id = ObjectId()
    cta5_id = ObjectId()

    cuentas = [
        {
            "_id": cta1_id,
            "cliente_id": cli1_id,
            "nombre": "Liderman - Sede San Isidro",
            "numero": "LID-001",
            "direccion": "Av. Javier Prado Este 4200",
            "distrito": "San Isidro",
            "contacto": "Jorge Ramírez",
            "telefono": "987001001",
            "tipo": "empresa",
            "latitud": -12.0950,
            "longitud": -77.0333,
            "activa": True,
            "created_at": _now(-55),
        },
        {
            "_id": cta2_id,
            "cliente_id": cli1_id,
            "nombre": "Liderman - Sede Miraflores",
            "numero": "LID-002",
            "direccion": "Av. Larco 1301",
            "distrito": "Miraflores",
            "contacto": "María Torres",
            "telefono": "987001002",
            "tipo": "empresa",
            "latitud": -12.1211,
            "longitud": -77.0302,
            "activa": True,
            "created_at": _now(-55),
        },
        {
            "_id": cta3_id,
            "cliente_id": cli2_id,
            "nombre": "BanBif - Agencia Centro",
            "numero": "BBF-001",
            "direccion": "Jr. de la Unión 600",
            "distrito": "Lima",
            "contacto": "Roberto Silva",
            "telefono": "987002001",
            "tipo": "empresa",
            "latitud": -12.0560,
            "longitud": -77.0295,
            "activa": True,
            "created_at": _now(-50),
        },
        {
            "_id": cta4_id,
            "cliente_id": cli2_id,
            "nombre": "BanBif - Agencia San Borja",
            "numero": "BBF-002",
            "direccion": "Av. San Borja Norte 793",
            "distrito": "San Borja",
            "contacto": "Elena Vargas",
            "telefono": "987002002",
            "tipo": "empresa",
            "latitud": -12.0892,
            "longitud": -77.0021,
            "activa": True,
            "created_at": _now(-50),
        },
        {
            "_id": cta5_id,
            "cliente_id": cli3_id,
            "nombre": "Cineplanet - Plaza Lima Norte",
            "numero": "CP-001",
            "direccion": "Av. Universitaria 6099",
            "distrito": "Comas",
            "contacto": "David Pinedo",
            "telefono": "987003001",
            "tipo": "empresa",
            "latitud": -11.9425,
            "longitud": -77.0590,
            "activa": True,
            "created_at": _now(-50),
        },
    ]
    for c in cuentas:
        db.cuentas.update_one(
            {"cliente_id": c["cliente_id"], "numero": c["numero"]},
            {"$setOnInsert": c},
            upsert=True,
        )
    print(f"   {len(cuentas)} cuentas OK.")

    # ================================================================
    # INVENTARIO
    # ================================================================
    print("→ Creando inventario...")
    items_inv = [
        # EPPs
        {"sku": "EPP-001", "nombre": "Casco de seguridad", "descripcion": "Casco ABS clase E", "categoria": "epp", "unidad": "unidad", "precio_unitario": 45.00, "stock_disponible": 20, "stock_minimo": 5},
        {"sku": "EPP-002", "nombre": "Chaleco reflectivo", "descripcion": "Chaleco naranja alta visibilidad", "categoria": "epp", "unidad": "unidad", "precio_unitario": 25.00, "stock_disponible": 30, "stock_minimo": 8},
        {"sku": "EPP-003", "nombre": "Guantes dieléctricos", "descripcion": "Guantes aislantes 1000V", "categoria": "epp", "unidad": "par", "precio_unitario": 38.50, "stock_disponible": 15, "stock_minimo": 4},
        {"sku": "EPP-004", "nombre": "Zapatos dieléctricos", "descripcion": "Zapatos de seguridad punta acero", "categoria": "epp", "unidad": "par", "precio_unitario": 120.00, "stock_disponible": 10, "stock_minimo": 3},
        # Materiales de red
        {"sku": "MAT-001", "nombre": "Cable UTP Cat6 (rollo 305m)", "descripcion": "Cable de red Cat6 sin blindaje", "categoria": "material", "unidad": "rollo", "precio_unitario": 280.00, "stock_disponible": 8, "stock_minimo": 2},
        {"sku": "MAT-002", "nombre": "Conector RJ45 (bolsa 100)", "descripcion": "Conectores RJ45 Cat6 sin blindaje", "categoria": "material", "unidad": "bolsa", "precio_unitario": 35.00, "stock_disponible": 25, "stock_minimo": 5},
        {"sku": "MAT-003", "nombre": "Switch 8 puertos Gigabit", "descripcion": "Switch no administrable 8p 10/100/1000", "categoria": "material", "unidad": "unidad", "precio_unitario": 185.00, "stock_disponible": 6, "stock_minimo": 2},
        {"sku": "MAT-004", "nombre": "Patch cord Cat6 1m", "descripcion": "Cable patch cord 1 metro azul", "categoria": "material", "unidad": "unidad", "precio_unitario": 8.00, "stock_disponible": 50, "stock_minimo": 10},
        # Cámaras y seguridad
        {"sku": "CAM-001", "nombre": "Cámara IP bullet 2MP", "descripcion": "Cámara exterior IP66 H.265 IR 30m", "categoria": "material", "unidad": "unidad", "precio_unitario": 220.00, "stock_disponible": 12, "stock_minimo": 3},
        {"sku": "CAM-002", "nombre": "Cámara IP domo 2MP", "descripcion": "Cámara domo interior IP H.265 IR 20m", "categoria": "material", "unidad": "unidad", "precio_unitario": 195.00, "stock_disponible": 9, "stock_minimo": 3},
        {"sku": "CAM-003", "nombre": "DVR 8 canales", "descripcion": "Grabador DVR H.265+ 8CH 1080P", "categoria": "material", "unidad": "unidad", "precio_unitario": 450.00, "stock_disponible": 4, "stock_minimo": 1},
        # Herramientas
        {"sku": "HER-001", "nombre": "Ponchadora RJ45", "descripcion": "Ponchadora crimping para RJ45/RJ11", "categoria": "herramienta", "unidad": "unidad", "precio_unitario": 28.00, "stock_disponible": 8, "stock_minimo": 2},
        {"sku": "HER-002", "nombre": "Tester de red UTP", "descripcion": "Tester básico para cable de red", "categoria": "herramienta", "unidad": "unidad", "precio_unitario": 45.00, "stock_disponible": 5, "stock_minimo": 2},
        # Control de accesos
        {"sku": "ACC-001", "nombre": "Control de acceso biométrico", "descripcion": "Terminal huella + tarjeta RFID", "categoria": "material", "unidad": "unidad", "precio_unitario": 380.00, "stock_disponible": 3, "stock_minimo": 1},
        {"sku": "ACC-002", "nombre": "Lector de tarjetas RFID", "descripcion": "Lector RFID 125KHz Wiegand 26bits", "categoria": "material", "unidad": "unidad", "precio_unitario": 95.00, "stock_disponible": 7, "stock_minimo": 2},
    ]
    inv_ids = {}
    for item in items_inv:
        item["activo"] = True
        item["created_at"] = _now(-45)
        item["updated_at"] = _now(-45)
        result = db.inventario.update_one({"sku": item["sku"]}, {"$setOnInsert": item}, upsert=True)
        doc = db.inventario.find_one({"sku": item["sku"]})
        inv_ids[item["sku"]] = doc["_id"]
    print(f"   {len(items_inv)} ítems de inventario OK.")

    # ================================================================
    # PEDIDOS — en diferentes fases para probar el flujo
    # ================================================================
    print("→ Creando pedidos de prueba...")

    def checklist_completo():
        from apps.pedidos.services import CHECKLIST_STEPS
        return [
            {**s, "completado": True, "nota": "Listo.", "completado_en": _now(-2)}
            for s in CHECKLIST_STEPS
        ]

    def checklist_vacio():
        from apps.pedidos.services import CHECKLIST_STEPS
        return [
            {**s, "completado": False, "nota": "", "completado_en": None}
            for s in CHECKLIST_STEPS
        ]

    def checklist_parcial():
        from apps.pedidos.services import CHECKLIST_STEPS
        steps = []
        for i, s in enumerate(CHECKLIST_STEPS):
            steps.append({**s, "completado": i < 2, "nota": "OK" if i < 2 else "", "completado_en": _now(-1) if i < 2 else None})
        return steps

    pedidos = [
        # 1. Pedido crítico sin técnico asignado
        {
            "codigo": "P0001",
            "cliente_id": cli1_id, "cuenta_id": cta1_id,
            "cliente_nombre": "Liderman S.A.", "cuenta_nombre": "Liderman - Sede San Isidro",
            "titulo": "Falla en sistema CCTV sede principal",
            "descripcion": "El sistema de cámaras del piso 3 al 7 no graba desde ayer. Se requiere revisión urgente del DVR y cableado.",
            "tipo_servicio": "Mantenimiento CCTV",
            "zona": "Lima Norte",
            "prioridad": "critica",
            "fase": "creacion",
            "estado": "por-confirmar",
            "tecnico_asignado_id": None, "tecnico_nombre": None,
            "epps_asignados": [],
            "materiales_requeridos": [],
            "checklist": checklist_vacio(),
            "evidencias": [],
            "diagnostico_tecnico": "",
            "materiales_usados": [],
            "costo_epps": 0.0, "costo_materiales": 0.0, "costo_total": 0.0,
            "informe": None,
            "motivo_rechazo": None, "historial_rechazos": [],
            "fecha_programada": _now(1),
            "fecha_inicio_labor": None, "fecha_fin_labor": None, "fecha_cierre": None,
            "created_at": _now(-1), "updated_at": _now(-1),
            "historial": [{"evento": "creacion", "detalle": "Pedido creado por coordinador1", "usuario": "coordinador1", "at": _now(-1)}],
        },
        # 2. Pedido alta prioridad — técnico asignado, pendiente de confirmar
        {
            "codigo": "P0002",
            "cliente_id": cli2_id, "cuenta_id": cta3_id,
            "cliente_nombre": "BanBif S.A.", "cuenta_nombre": "BanBif - Agencia Centro",
            "titulo": "Instalación de red LAN en nueva oficina",
            "descripcion": "Tendido de 20 puntos de red Cat6, configuración de switch y patch panel.",
            "tipo_servicio": "Instalación de Red",
            "zona": "Lima Centro",
            "prioridad": "alta",
            "fase": "creacion",
            "estado": "por-confirmar",
            "tecnico_asignado_id": tec1_id,
            "tecnico_nombre": "Pedro Huanca Flores",
            "epps_asignados": [
                {"item_id": inv_ids["EPP-001"], "sku": "EPP-001", "nombre": "Casco de seguridad", "cantidad": 1, "precio_unitario": 45.00},
                {"item_id": inv_ids["EPP-002"], "sku": "EPP-002", "nombre": "Chaleco reflectivo", "cantidad": 1, "precio_unitario": 25.00},
            ],
            "materiales_requeridos": [
                {"item_id": inv_ids["MAT-001"], "sku": "MAT-001", "nombre": "Cable UTP Cat6 (rollo 305m)", "cantidad": 2, "precio_unitario": 280.00},
                {"item_id": inv_ids["MAT-002"], "sku": "MAT-002", "nombre": "Conector RJ45 (bolsa 100)", "cantidad": 3, "precio_unitario": 35.00},
            ],
            "checklist": checklist_vacio(),
            "evidencias": [],
            "diagnostico_tecnico": "",
            "materiales_usados": [],
            "costo_epps": 70.00, "costo_materiales": 0.0, "costo_total": 70.00,
            "informe": None,
            "motivo_rechazo": None, "historial_rechazos": [],
            "fecha_programada": _now(2),
            "fecha_inicio_labor": None, "fecha_fin_labor": None, "fecha_cierre": None,
            "created_at": _now(-2), "updated_at": _now(-2),
            "historial": [
                {"evento": "creacion", "detalle": "Creado por coordinador1", "usuario": "coordinador1", "at": _now(-2)},
                {"evento": "asignacion", "detalle": "Técnico 'Pedro Huanca Flores' asignado", "usuario": "coordinador1", "at": _now(-2)},
            ],
        },
        # 3. Pedido rechazado — listo para reasignar
        {
            "codigo": "P0003",
            "cliente_id": cli1_id, "cuenta_id": cta2_id,
            "cliente_nombre": "Liderman S.A.", "cuenta_nombre": "Liderman - Sede Miraflores",
            "titulo": "Ampliación de cámaras piso 2",
            "descripcion": "Instalar 4 cámaras adicionales en el pasillo del piso 2.",
            "tipo_servicio": "Instalación CCTV",
            "zona": "Lima Centro",
            "prioridad": "media",
            "fase": "creacion",
            "estado": "rechazado",
            "tecnico_asignado_id": tec3_id,
            "tecnico_nombre": "Rosa Mamani Condori",
            "epps_asignados": [
                {"item_id": inv_ids["EPP-002"], "sku": "EPP-002", "nombre": "Chaleco reflectivo", "cantidad": 1, "precio_unitario": 25.00},
            ],
            "materiales_requeridos": [
                {"item_id": inv_ids["CAM-002"], "sku": "CAM-002", "nombre": "Cámara IP domo 2MP", "cantidad": 4, "precio_unitario": 195.00},
            ],
            "checklist": checklist_vacio(),
            "evidencias": [],
            "diagnostico_tecnico": "",
            "materiales_usados": [],
            "costo_epps": 25.00, "costo_materiales": 0.0, "costo_total": 25.00,
            "informe": None,
            "motivo_rechazo": "No tengo disponibilidad ese día, estoy en otra instalación.",
            "historial_rechazos": [
                {"tecnico_nombre": "Rosa Mamani Condori", "motivo": "No tengo disponibilidad ese día.", "at": _now(-1)},
            ],
            "fecha_programada": _now(3),
            "fecha_inicio_labor": None, "fecha_fin_labor": None, "fecha_cierre": None,
            "created_at": _now(-3), "updated_at": _now(-1),
            "historial": [
                {"evento": "creacion", "detalle": "Creado por coordinador2", "usuario": "coordinador2", "at": _now(-3)},
                {"evento": "asignacion", "detalle": "Técnico 'Rosa Mamani Condori' asignado", "usuario": "coordinador2", "at": _now(-3)},
                {"evento": "rechazo", "detalle": "Rechazado por Rosa Mamani Condori", "usuario": "tecnico3", "at": _now(-1)},
            ],
        },
        # 4. Pedido confirmado — técnico va a ejecutar
        {
            "codigo": "P0004",
            "cliente_id": cli3_id, "cuenta_id": cta5_id,
            "cliente_nombre": "Cineplanet S.A.", "cuenta_nombre": "Cineplanet - Plaza Lima Norte",
            "titulo": "Mantenimiento preventivo red LAN",
            "descripcion": "Revisión y limpieza de rack, verificación de cables y actualización de firmware en switches.",
            "tipo_servicio": "Mantenimiento de Red",
            "zona": "Lima Norte",
            "prioridad": "media",
            "fase": "programacion",
            "estado": "confirmado",
            "tecnico_asignado_id": tec1_id,
            "tecnico_nombre": "Pedro Huanca Flores",
            "epps_asignados": [
                {"item_id": inv_ids["EPP-001"], "sku": "EPP-001", "nombre": "Casco de seguridad", "cantidad": 1, "precio_unitario": 45.00},
                {"item_id": inv_ids["EPP-003"], "sku": "EPP-003", "nombre": "Guantes dieléctricos", "cantidad": 1, "precio_unitario": 38.50},
            ],
            "materiales_requeridos": [
                {"item_id": inv_ids["MAT-004"], "sku": "MAT-004", "nombre": "Patch cord Cat6 1m", "cantidad": 5, "precio_unitario": 8.00},
            ],
            "checklist": checklist_vacio(),
            "evidencias": [],
            "diagnostico_tecnico": "",
            "materiales_usados": [],
            "costo_epps": 83.50, "costo_materiales": 0.0, "costo_total": 83.50,
            "informe": None,
            "motivo_rechazo": None, "historial_rechazos": [],
            "fecha_programada": _now(0),
            "fecha_inicio_labor": None, "fecha_fin_labor": None, "fecha_cierre": None,
            "created_at": _now(-4), "updated_at": _now(-1),
            "historial": [
                {"evento": "creacion", "detalle": "Creado por coordinador1", "usuario": "coordinador1", "at": _now(-4)},
                {"evento": "asignacion", "detalle": "Técnico asignado", "usuario": "coordinador1", "at": _now(-3)},
                {"evento": "confirmacion", "detalle": "Confirmado por Pedro Huanca Flores", "usuario": "tecnico1", "at": _now(-1)},
            ],
        },
        # 5. Pedido en labor — checklist parcialmente completo
        {
            "codigo": "P0005",
            "cliente_id": cli2_id, "cuenta_id": cta4_id,
            "cliente_nombre": "BanBif S.A.", "cuenta_nombre": "BanBif - Agencia San Borja",
            "titulo": "Instalación sistema de control de acceso",
            "descripcion": "Instalación de lector biométrico en ingreso principal y 2 lectores RFID en puertas secundarias.",
            "tipo_servicio": "Control de Accesos",
            "zona": "Lima Sur",
            "prioridad": "alta",
            "fase": "seguimiento",
            "estado": "en-labor",
            "tecnico_asignado_id": tec2_id,
            "tecnico_nombre": "Luis García Vega",
            "epps_asignados": [
                {"item_id": inv_ids["EPP-002"], "sku": "EPP-002", "nombre": "Chaleco reflectivo", "cantidad": 1, "precio_unitario": 25.00},
                {"item_id": inv_ids["EPP-004"], "sku": "EPP-004", "nombre": "Zapatos dieléctricos", "cantidad": 1, "precio_unitario": 120.00},
            ],
            "materiales_requeridos": [
                {"item_id": inv_ids["ACC-001"], "sku": "ACC-001", "nombre": "Control de acceso biométrico", "cantidad": 1, "precio_unitario": 380.00},
                {"item_id": inv_ids["ACC-002"], "sku": "ACC-002", "nombre": "Lector de tarjetas RFID", "cantidad": 2, "precio_unitario": 95.00},
            ],
            "checklist": checklist_parcial(),
            "evidencias": [
                {"id": str(ObjectId()), "nombre": "antes_ingreso.jpg", "archivo": "evidencias/P0005/antes/antes_ingreso.jpg", "descripcion": "Estado inicial del ingreso", "stage": "antes", "subida_por": "tecnico2", "uploaded_at": _now(-1)},
            ],
            "diagnostico_tecnico": "Panel de control deteriorado. Se procederá con la instalación del nuevo sistema biométrico.",
            "materiales_usados": [],
            "costo_epps": 145.00, "costo_materiales": 0.0, "costo_total": 145.00,
            "informe": None,
            "motivo_rechazo": None, "historial_rechazos": [],
            "fecha_programada": _now(-2),
            "fecha_inicio_labor": _now(-1), "fecha_fin_labor": None, "fecha_cierre": None,
            "created_at": _now(-5), "updated_at": _now(-1),
            "historial": [
                {"evento": "creacion", "detalle": "Creado por admin", "usuario": "admin", "at": _now(-5)},
                {"evento": "asignacion", "detalle": "Técnico asignado", "usuario": "admin", "at": _now(-4)},
                {"evento": "confirmacion", "detalle": "Confirmado por Luis García Vega", "usuario": "tecnico2", "at": _now(-3)},
                {"evento": "checklist", "detalle": "Materiales listos verificados", "usuario": "tecnico2", "at": _now(-2)},
                {"evento": "evidencia", "detalle": "Foto 'antes' subida", "usuario": "tecnico2", "at": _now(-1)},
            ],
        },
        # 6. Pedido completado
        {
            "codigo": "P0006",
            "cliente_id": cli1_id, "cuenta_id": cta1_id,
            "cliente_nombre": "Liderman S.A.", "cuenta_nombre": "Liderman - Sede San Isidro",
            "titulo": "Configuración de VPN site-to-site",
            "descripcion": "Configurar VPN entre sede principal y sucursal Miraflores.",
            "tipo_servicio": "Configuración de Red",
            "zona": "Lima Centro",
            "prioridad": "media",
            "fase": "cierre",
            "estado": "completado",
            "tecnico_asignado_id": tec1_id,
            "tecnico_nombre": "Pedro Huanca Flores",
            "epps_asignados": [
                {"item_id": inv_ids["EPP-001"], "sku": "EPP-001", "nombre": "Casco de seguridad", "cantidad": 1, "precio_unitario": 45.00},
            ],
            "materiales_requeridos": [],
            "checklist": checklist_completo(),
            "evidencias": [
                {"id": str(ObjectId()), "nombre": "antes_rack.jpg", "archivo": "evidencias/P0006/antes/antes_rack.jpg", "descripcion": "Rack antes de configuración", "stage": "antes", "subida_por": "tecnico1", "uploaded_at": _now(-8)},
                {"id": str(ObjectId()), "nombre": "despues_rack.jpg", "archivo": "evidencias/P0006/despues/despues_rack.jpg", "descripcion": "Rack configurado correctamente", "stage": "despues", "subida_por": "tecnico1", "uploaded_at": _now(-7)},
            ],
            "diagnostico_tecnico": "VPN configurada exitosamente. Se probó conectividad bidireccional y latencia aceptable.",
            "materiales_usados": [
                {"item_id": inv_ids["MAT-004"], "sku": "MAT-004", "nombre": "Patch cord Cat6 1m", "cantidad": 2, "precio_unitario": 8.00},
            ],
            "costo_epps": 45.00, "costo_materiales": 16.00, "costo_total": 61.00,
            "informe": {
                "diagnostico_final": "VPN site-to-site configurada y operativa. Latencia promedio 12ms.",
                "responsable_local": "Jorge Ramírez",
                "pedido_solicitado": "Configuración VPN entre sedes",
                "observaciones": "Se detectó que el firewall tenía reglas desactualizadas, se corrigió durante la visita.",
                "recomendaciones": "Programar revisión semestral de políticas de seguridad en ambos firewalls.",
                "firma_cliente": None,
                "created_at": _now(-6),
            },
            "motivo_rechazo": None, "historial_rechazos": [],
            "fecha_programada": _now(-10),
            "fecha_inicio_labor": _now(-9), "fecha_fin_labor": _now(-7), "fecha_cierre": _now(-6),
            "created_at": _now(-12), "updated_at": _now(-6),
            "historial": [
                {"evento": "creacion", "detalle": "Creado por coordinador1", "usuario": "coordinador1", "at": _now(-12)},
                {"evento": "asignacion", "detalle": "Técnico asignado", "usuario": "coordinador1", "at": _now(-11)},
                {"evento": "confirmacion", "detalle": "Confirmado por Pedro Huanca Flores", "usuario": "tecnico1", "at": _now(-10)},
                {"evento": "checklist", "detalle": "Checklist completado", "usuario": "tecnico1", "at": _now(-9)},
                {"evento": "evidencia", "detalle": "Foto 'antes' subida", "usuario": "tecnico1", "at": _now(-8)},
                {"evento": "evidencia", "detalle": "Foto 'después' subida", "usuario": "tecnico1", "at": _now(-7)},
                {"evento": "informe", "detalle": "Informe técnico completado", "usuario": "tecnico1", "at": _now(-6)},
                {"evento": "completado", "detalle": "Completado por coordinador1", "usuario": "coordinador1", "at": _now(-6)},
            ],
        },
        # 7. Pedido dado de baja
        {
            "codigo": "P0007",
            "cliente_id": cli3_id, "cuenta_id": cta5_id,
            "cliente_nombre": "Cineplanet S.A.", "cuenta_nombre": "Cineplanet - Plaza Lima Norte",
            "titulo": "Actualización firmware cámaras",
            "descripcion": "Actualizar firmware en 12 cámaras IP del local.",
            "tipo_servicio": "Mantenimiento CCTV",
            "zona": "Lima Norte",
            "prioridad": "baja",
            "fase": "cierre",
            "estado": "dado-de-baja",
            "tecnico_asignado_id": tec3_id,
            "tecnico_nombre": "Rosa Mamani Condori",
            "epps_asignados": [],
            "materiales_requeridos": [],
            "checklist": checklist_vacio(),
            "evidencias": [],
            "diagnostico_tecnico": "",
            "materiales_usados": [],
            "costo_epps": 0.0, "costo_materiales": 0.0, "costo_total": 0.0,
            "informe": None,
            "motivo_rechazo": "Cliente canceló el servicio. No requiere la actualización por ahora.",
            "historial_rechazos": [],
            "fecha_programada": _now(-5),
            "fecha_inicio_labor": None, "fecha_fin_labor": None, "fecha_cierre": None,
            "created_at": _now(-7), "updated_at": _now(-4),
            "historial": [
                {"evento": "creacion", "detalle": "Creado por admin", "usuario": "admin", "at": _now(-7)},
                {"evento": "baja", "detalle": "Dado de baja: Cliente canceló el servicio.", "usuario": "coordinador2", "at": _now(-4)},
            ],
        },
        # 8. Pedido con informe pendiente de cerrar (cierre-tecnico)
        {
            "codigo": "P0008",
            "cliente_id": cli2_id, "cuenta_id": cta3_id,
            "cliente_nombre": "BanBif S.A.", "cuenta_nombre": "BanBif - Agencia Centro",
            "titulo": "Instalación de 6 cámaras PTZ exterior",
            "descripcion": "Montaje e instalación de 6 cámaras PTZ en el perímetro del edificio.",
            "tipo_servicio": "Instalación CCTV",
            "zona": "Lima Centro",
            "prioridad": "alta",
            "fase": "cierre",
            "estado": "cierre-tecnico",
            "tecnico_asignado_id": tec2_id,
            "tecnico_nombre": "Luis García Vega",
            "epps_asignados": [
                {"item_id": inv_ids["EPP-001"], "sku": "EPP-001", "nombre": "Casco de seguridad", "cantidad": 1, "precio_unitario": 45.00},
                {"item_id": inv_ids["EPP-002"], "sku": "EPP-002", "nombre": "Chaleco reflectivo", "cantidad": 1, "precio_unitario": 25.00},
            ],
            "materiales_requeridos": [
                {"item_id": inv_ids["CAM-001"], "sku": "CAM-001", "nombre": "Cámara IP bullet 2MP", "cantidad": 6, "precio_unitario": 220.00},
            ],
            "checklist": checklist_completo(),
            "evidencias": [
                {"id": str(ObjectId()), "nombre": "antes_exterior.jpg", "archivo": "evidencias/P0008/antes/antes_exterior.jpg", "descripcion": "Estado exterior antes", "stage": "antes", "subida_por": "tecnico2", "uploaded_at": _now(-3)},
                {"id": str(ObjectId()), "nombre": "despues_camaras.jpg", "archivo": "evidencias/P0008/despues/despues_camaras.jpg", "descripcion": "Cámaras instaladas", "stage": "despues", "subida_por": "tecnico2", "uploaded_at": _now(-2)},
            ],
            "diagnostico_tecnico": "6 cámaras PTZ instaladas y configuradas. Todas operativas.",
            "materiales_usados": [
                {"item_id": inv_ids["CAM-001"], "sku": "CAM-001", "nombre": "Cámara IP bullet 2MP", "cantidad": 6, "precio_unitario": 220.00},
                {"item_id": inv_ids["MAT-004"], "sku": "MAT-004", "nombre": "Patch cord Cat6 1m", "cantidad": 6, "precio_unitario": 8.00},
            ],
            "costo_epps": 70.00, "costo_materiales": 1368.00, "costo_total": 1438.00,
            "informe": {
                "diagnostico_final": "Instalación completada. 6 cámaras PTZ operativas con visión panorámica del perímetro.",
                "responsable_local": "Roberto Silva",
                "pedido_solicitado": "Instalación cámaras PTZ perímetro",
                "observaciones": "Se detectó humedad en la pared norte. Se recomienda impermeabilización antes de siguiente instalación.",
                "recomendaciones": "Mantenimiento preventivo en 6 meses.",
                "firma_cliente": None,
                "created_at": _now(-2),
            },
            "motivo_rechazo": None, "historial_rechazos": [],
            "fecha_programada": _now(-5),
            "fecha_inicio_labor": _now(-3), "fecha_fin_labor": _now(-2), "fecha_cierre": None,
            "created_at": _now(-7), "updated_at": _now(-2),
            "historial": [
                {"evento": "creacion", "detalle": "Creado por coordinador2", "usuario": "coordinador2", "at": _now(-7)},
                {"evento": "asignacion", "detalle": "Técnico asignado", "usuario": "coordinador2", "at": _now(-6)},
                {"evento": "confirmacion", "detalle": "Confirmado por Luis García Vega", "usuario": "tecnico2", "at": _now(-5)},
                {"evento": "checklist", "detalle": "Checklist completado", "usuario": "tecnico2", "at": _now(-4)},
                {"evento": "informe", "detalle": "Informe enviado, pendiente de cierre", "usuario": "tecnico2", "at": _now(-2)},
            ],
        },
    ]

    for p in pedidos:
        db.pedidos.update_one({"codigo": p["codigo"]}, {"$setOnInsert": p}, upsert=True)
    print(f"   {len(pedidos)} pedidos OK.")

    # ================================================================
    # NOTIFICACIONES iniciales
    # ================================================================
    print("→ Creando notificaciones de prueba...")
    tec1_db = db.tecnicos.find_one({"user_id": tec1_user_id})
    tec1_user = db.users.find_one({"_id": tec1_user_id})
    tec2_user = db.users.find_one({"_id": tec2_user_id})

    notifs = [
        {
            "tipo": "pedido_por_confirmar",
            "titulo": "Nuevo pedido asignado",
            "mensaje": "Se te asignó el pedido P0002: Instalación de red LAN en nueva oficina",
            "para_rol": None,
            "para_user_id": tec1_user["_id"] if tec1_user else None,
            "pedido_id": db.pedidos.find_one({"codigo": "P0002"})["_id"] if db.pedidos.find_one({"codigo": "P0002"}) else None,
            "leida": False,
            "created_at": _now(-2),
        },
        {
            "tipo": "pedido_rechazado",
            "titulo": "Pedido rechazado",
            "mensaje": "Rosa Mamani Condori rechazó el pedido P0003. Motivo: No tengo disponibilidad ese día.",
            "para_rol": "coordinador",
            "para_user_id": None,
            "pedido_id": db.pedidos.find_one({"codigo": "P0003"})["_id"] if db.pedidos.find_one({"codigo": "P0003"}) else None,
            "leida": False,
            "created_at": _now(-1),
        },
        {
            "tipo": "pedido_completado",
            "titulo": "Pedido completado",
            "mensaje": "El pedido P0006 fue completado exitosamente.",
            "para_rol": "todos",
            "para_user_id": None,
            "pedido_id": db.pedidos.find_one({"codigo": "P0006"})["_id"] if db.pedidos.find_one({"codigo": "P0006"}) else None,
            "leida": True,
            "created_at": _now(-6),
        },
    ]
    for n in notifs:
        db.notificaciones.insert_one(n)
    print(f"   {len(notifs)} notificaciones OK.")

    print("\n✅ Seed completado exitosamente.")
    print("   Accede con cualquiera de los usuarios listados arriba.")


if __name__ == "__main__":
    reset = "--reset" in sys.argv
    run(reset=reset)

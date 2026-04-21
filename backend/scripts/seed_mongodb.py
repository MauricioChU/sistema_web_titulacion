import argparse
import json
from datetime import datetime, timezone

from pymongo import ASCENDING, MongoClient


def seed_database(uri: str, db_name: str):
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")

    client.drop_database(db_name)
    db = client[db_name]

    now = datetime.now(timezone.utc)

    clientes = [
        {
            "_id": "cli_001",
            "nombre": "Clinica Miraflores",
            "documento": "20548796321",
            "telefono": "987123111",
            "correo": "laura.medina@clinicamf.pe",
            "direccion": "Av. Arequipa 1001",
            "activo": True,
            "created_at": now,
        },
        {
            "_id": "cli_002",
            "nombre": "Condominio Brisas",
            "documento": "20600154789",
            "telefono": "965774100",
            "correo": "administracion@brisas.pe",
            "direccion": "Calle Parque Norte 450",
            "activo": True,
            "created_at": now,
        },
    ]

    cuentas = [
        {
            "_id": "cta_001",
            "cliente_id": "cli_001",
            "nombre": "Sede Principal",
            "numero": "CUE-1001",
            "tipo": "empresa",
            "latitud": -12.1211,
            "longitud": -77.0297,
            "activa": True,
            "created_at": now,
        },
        {
            "_id": "cta_002",
            "cliente_id": "cli_002",
            "nombre": "Torre A",
            "numero": "CUE-2001",
            "tipo": "hogar",
            "latitud": -12.1405,
            "longitud": -76.9910,
            "activa": True,
            "created_at": now,
        },
    ]

    tecnicos = [
        {
            "_id": "tec_001",
            "nombre": "Luis Rojas",
            "especialidad": "Electrico industrial",
            "zona": "Miraflores",
            "latitud_base": -12.1211,
            "longitud_base": -77.0297,
            "capacidad_diaria": 5,
            "activo": True,
            "created_at": now,
        },
        {
            "_id": "tec_002",
            "nombre": "Carlos Palacios",
            "especialidad": "UPS y tableros",
            "zona": "La Molina",
            "latitud_base": -12.0749,
            "longitud_base": -76.9512,
            "capacidad_diaria": 4,
            "activo": True,
            "created_at": now,
        },
    ]

    pedidos = [
        {
            "_id": "ped_001",
            "code": "A0001",
            "cliente_id": "cli_001",
            "cuenta_id": "cta_001",
            "tecnico_asignado_id": "tec_001",
            "titulo": "Mantenimiento electrico integral",
            "descripcion": "Seed para pruebas en MongoDB",
            "tipo_servicio": "mantenimiento electrico",
            "zona": "Miraflores",
            "prioridad": "alta",
            "fase": "seguimiento",
            "status_operativo": "en-labor",
            "subfase_tecnica": "evidencias",
            "diagnostico_tecnico": "Diagnostico preliminar en progreso",
            "historial": [
                {
                    "evento": "seed",
                    "usuario": "system",
                    "detalle": "Pedido inicial de prueba",
                    "timestamp": now.isoformat(),
                }
            ],
            "created_at": now,
            "updated_at": now,
        },
        {
            "_id": "ped_002",
            "code": "A0002",
            "cliente_id": "cli_002",
            "cuenta_id": "cta_002",
            "tecnico_asignado_id": "tec_002",
            "titulo": "Mantenimiento de UPS",
            "descripcion": "Pedido seed para flujo tecnico",
            "tipo_servicio": "mantenimiento ups",
            "zona": "La Molina",
            "prioridad": "media",
            "fase": "programacion",
            "status_operativo": "confirmado",
            "subfase_tecnica": "ejecucion",
            "diagnostico_tecnico": "Pendiente de visita",
            "historial": [
                {
                    "evento": "seed",
                    "usuario": "system",
                    "detalle": "Pedido planificado",
                    "timestamp": now.isoformat(),
                }
            ],
            "created_at": now,
            "updated_at": now,
        },
    ]

    checklist_steps = [
        {
            "_id": "chk_001",
            "pedido_id": "ped_001",
            "tecnico_id": "tec_001",
            "step_id": "materiales-listos",
            "completado": True,
            "nota": "Material listo",
            "completado_en": now,
            "created_at": now,
        },
        {
            "_id": "chk_002",
            "pedido_id": "ped_001",
            "tecnico_id": "tec_001",
            "step_id": "llegada-sitio",
            "completado": True,
            "nota": "Llegada confirmada",
            "completado_en": now,
            "created_at": now,
        },
    ]

    evidencias = [
        {
            "_id": "ev_001",
            "pedido_id": "ped_001",
            "tecnico_id": "tec_001",
            "nombre": "antes.jpg",
            "archivo": "evidencias/2026/04/18/antes.jpg",
            "descripcion": "Estado inicial del tablero",
            "stage": "antes",
            "source": "archivo",
            "created_at": now,
        },
        {
            "_id": "ev_002",
            "pedido_id": "ped_001",
            "tecnico_id": "tec_001",
            "nombre": "despues.jpg",
            "archivo": "evidencias/2026/04/18/despues.jpg",
            "descripcion": "Estado final del tablero",
            "stage": "despues",
            "source": "archivo",
            "created_at": now,
        },
    ]

    informes_tecnicos = [
        {
            "_id": "inf_001",
            "pedido_id": "ped_001",
            "tecnico_id": "tec_001",
            "diagnostico_final": "Se corrigio sobrecarga y conexion floja",
            "responsable_local": "Laura Medina",
            "pedido_solicitado": "Mantenimiento electrico integral",
            "observaciones": "Operacion estable al cierre",
            "recomendaciones": "Inspeccion mensual",
            "firma_cliente": "firmas/2026/04/18/firma_001.png",
            "created_at": now,
            "updated_at": now,
        }
    ]

    db.clientes.insert_many(clientes)
    db.cuentas.insert_many(cuentas)
    db.tecnicos.insert_many(tecnicos)
    db.pedidos.insert_many(pedidos)
    db.checklist_steps.insert_many(checklist_steps)
    db.evidencias.insert_many(evidencias)
    db.informes_tecnicos.insert_many(informes_tecnicos)

    db.clientes.create_index([("documento", ASCENDING)], unique=True)
    db.cuentas.create_index([("numero", ASCENDING)], unique=True)
    db.pedidos.create_index([("code", ASCENDING)], unique=True)
    db.pedidos.create_index([("tecnico_asignado_id", ASCENDING)])
    db.pedidos.create_index([("fase", ASCENDING), ("status_operativo", ASCENDING)])

    summary = {
        "ok": True,
        "mongo_uri": uri,
        "database": db_name,
        "collections": sorted(db.list_collection_names()),
        "counts": {
            "clientes": db.clientes.count_documents({}),
            "cuentas": db.cuentas.count_documents({}),
            "tecnicos": db.tecnicos.count_documents({}),
            "pedidos": db.pedidos.count_documents({}),
            "checklist_steps": db.checklist_steps.count_documents({}),
            "evidencias": db.evidencias.count_documents({}),
            "informes_tecnicos": db.informes_tecnicos.count_documents({}),
        },
        "sample_pedido": db.pedidos.find_one(
            {"_id": "ped_001"},
            {
                "_id": 1,
                "code": 1,
                "fase": 1,
                "status_operativo": 1,
                "subfase_tecnica": 1,
                "tecnico_asignado_id": 1,
            },
        ),
    }

    client.close()
    return summary


def main():
    parser = argparse.ArgumentParser(description="Reset + seed MongoDB para titulacion_db")
    parser.add_argument("--uri", default="mongodb://localhost:27017", help="Mongo URI")
    parser.add_argument("--db", default="titulacion_db", help="Nombre de base de datos")
    args = parser.parse_args()

    try:
        result = seed_database(args.uri, args.db)
        print(json.dumps(result, ensure_ascii=True, indent=2, default=str))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=True, indent=2))
        raise


if __name__ == "__main__":
    main()

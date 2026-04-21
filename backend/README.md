# Backend Django Simplificado (OT)

Backend REST construido con Django + DRF para reemplazar de forma simple partes del `ot-manager-api`.

## Alcance implementado

- CRUD de tecnicos
- CRUD de clientes
- CRUD de cuentas
- CRUD de pedidos
- Dashboard de resumen
- Recomendacion de tecnico mas adecuado para un pedido
- Autoasignacion de tecnico sugerido
- Fases simplificadas del pedido:
  - `creacion`
  - `programacion`
  - `seguimiento`
  - `cierre`

## Estructura

- `config/`: configuracion Django
- `apps/core`: health check
- `apps/tecnicos`: modelo y CRUD de tecnicos
- `apps/clientes`: modelo y CRUD de clientes
- `apps/cuentas`: modelo y CRUD de cuentas
- `apps/pedidos`: pedidos + acciones de recomendacion y autoasignacion
- `apps/recomendaciones`: logica de scoring
- `apps/dashboard`: endpoint de resumen

## Instalacion y ejecucion

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## Endpoints principales

- `GET /api/health/`
- `GET /api/docs/`
- `GET /api/schema/`

### CRUDs

- `/api/tecnicos/`
- `/api/clientes/`
- `/api/cuentas/`
- `/api/pedidos/`

### Dashboard

- `GET /api/dashboard/resumen/`

### Recomendacion

- `GET /api/recomendaciones/pedidos/{pedido_id}/tecnico-sugerido/`
- `POST /api/pedidos/{id}/recomendar_tecnico/`
- `POST /api/pedidos/{id}/auto_asignar/`

## Base de datos MongoDB (principal)

Este backend esta configurado para usar MongoDB como base de datos principal de Django.

Por defecto, el backend conecta a Mongo local con:

- `MONGODB_URI=mongodb://127.0.0.1:27017`
- `MONGODB_DB_NAME=sistema_titulacion`
- `MONGODB_PEDIDOS_COLLECTION=pedidos`
- `MONGODB_CLIENTES_COLLECTION=clientes`
- `MONGODB_CUENTAS_COLLECTION=cuentas`
- `MONGODB_TECNICOS_COLLECTION=tecnicos`

Si quieres valores personalizados, configura estas variables de entorno:

- `DJANGO_DB_ENGINE` (opcional, default: `django_mongodb_backend`)
- `MONGODB_URI` (ejemplo: `mongodb://localhost:27017`)
- `MONGODB_DB_NAME` (ejemplo: `sistema_titulacion`)
- `MONGODB_PEDIDOS_COLLECTION` (opcional, default: `pedidos`)
- `MONGODB_CLIENTES_COLLECTION` (opcional, default: `clientes`)
- `MONGODB_CUENTAS_COLLECTION` (opcional, default: `cuentas`)
- `MONGODB_TECNICOS_COLLECTION` (opcional, default: `tecnicos`)
- `MONGODB_SERVER_SELECTION_TIMEOUT_MS` (opcional, default: `3000`)

Si deseas desactivar la sincronizacion de colecciones espejo, define:

- `MONGODB_SYNC_ENABLED=false`

Con esas variables activas, el backend mantiene colecciones operativas y espejo en Mongo para:

- Crear/editar/eliminar pedido
- Crear/editar/eliminar cliente
- Crear/editar/eliminar cuenta
- Crear/editar/eliminar tecnico

## Prueba rapida (script Python)

Para validar rapidamente que `POST /api/pedidos/` crea el pedido y que queda sincronizado en Mongo, ejecuta:

```bash
cd backend
# Windows (venv local)
.venv\Scripts\python.exe scripts\verify_create_pedido.py

# Alternativa si no usas ese venv
python scripts\verify_create_pedido.py
```

Salida esperada:

- `"ok": true`
- `"pedido_id": <numero>`
- `"mongo_found": true`

Tambien puedes correrlo desde VS Code con la tarea:

- `Backend: Verify pedido create + Mongo`

## Prueba rapida (sync operacional con senales)

Para validar de extremo a extremo la sincronizacion Mongo de `clientes`, `cuentas` y `tecnicos` (create/update/delete), ejecuta:

```bash
cd backend
# Windows (venv local)
.venv\Scripts\python.exe scripts\verify_operational_mongo_sync.py

# Alternativa si no usas ese venv
python scripts\verify_operational_mongo_sync.py
```

Salida esperada:

- `"ok": true`
- `"updated_checks"` con valores actualizados
- `"delete_checks": "ok"`

## Logica de recomendacion

Scoring simple por tecnico activo:

- +40 si coincide `zona` con el pedido
- +35 si coincide `especialidad` con `tipo_servicio`
- +5 por cada cupo disponible hasta maximo +25

`cupo_disponible = capacidad_diaria - pedidos_abiertos`

Se consideran pedidos abiertos las fases: `creacion`, `programacion`, `seguimiento`.

## Nucleo recomendado (siguiente iteracion)

Para profesionalizar este backend, recomiendo agregar:

- Autenticacion JWT y roles (`admin`, `coordinador`, `tecnico`)
- Auditoria de cambios (historial por pedido)
- Reglas de transicion de fases (maquina de estados)
- Colas de tareas para notificaciones (Celery + Redis)
- Tests unitarios y de integracion con pytest

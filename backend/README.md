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

# Backend PROINTEL

Django 5.2 + DRF + SimpleJWT. Sin MongoDB, sin overhead: SQLite en dev, Postgres en prod.

## Stack

| Capa | Libreria |
|------|---------|
| Framework | Django 5.2 |
| API | djangorestframework 3.15 |
| Auth | djangorestframework-simplejwt 5.3 |
| CORS | django-cors-headers 4.4 |
| Filtros | django-filter 24.3 |
| Docs API | drf-spectacular 0.27 |
| Imagenes | Pillow 10.4 |

## Inicio rapido

```bash
# 1. Entorno virtual
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
.venv\Scripts\activate         # Windows

# 2. Dependencias
pip install -r requirements.txt

# 3. Variables de entorno
cp .env.example .env
# editar .env si es necesario

# 4. Base de datos + datos demo
python manage.py migrate
python manage.py seed_demo

# 5. Servidor
python manage.py runserver
```

Servidor en: http://127.0.0.1:8000

## Credenciales demo

| Usuario | Password | Rol |
|---------|----------|-----|
| admin | admin1234 | superadmin |
| coordinador1 | coord1234 | coordinador |
| tecnico1 | tec1234 | tecnico |
| tecnico2 | tec1234 | tecnico |

## Estructura de apps

```
apps/
  accounts/       — auth: login, refresh, /me + roles + permisos
  clientes/       — CRUD clientes corporativos
  cuentas/        — CRUD sedes/puntos operativos con coordenadas
  tecnicos/       — CRUD tecnicos de campo con ubicacion base
  inventario/     — CRUD items de inventario
  pedidos/        — workflow completo de pedidos (models + services + views)
  recomendaciones/— scoring haversine para sugerir tecnico
  dashboard/      — KPIs operativos agregados
  core/           — health check
```

## Patron arquitectonico: views delgadas + services

Las vistas solo se encargan de autenticacion/permisos, deserializacion y formateo de respuesta.
Toda la logica de negocio (transiciones de estado, validaciones cruzadas) vive en `services.py`.

```
PedidoViewSet.confirmar()
    └─► services.confirmar_pedido(pedido, tecnico=t, usuario=u)
            └─► pedido.fase = PROGRAMACION
            └─► pedido.status_operativo = CONFIRMADO
            └─► save_with_history(...)
            └─► TecnicoUpdate.objects.create(...)
```

## Contrato de API con el frontend

Base URL: `http://127.0.0.1:8000/api/`

### Auth
| Metodo | Path | Descripcion |
|--------|------|-------------|
| POST | auth/login/ | Obtener tokens JWT |
| POST | auth/refresh/ | Refrescar access token |
| GET | auth/me/ | Perfil del usuario autenticado |

### Recursos CRUD
| Recurso | Path base |
|---------|-----------|
| Clientes | clientes/ |
| Cuentas | cuentas/ |
| Tecnicos | tecnicos/ |
| Inventario | inventario/ |
| Pedidos | pedidos/ |

### Acciones de workflow (pedidos)
| Metodo | Path | Actor | Descripcion |
|--------|------|-------|-------------|
| POST | pedidos/{id}/confirmar/ | Tecnico | Acepta el pedido |
| POST | pedidos/{id}/checklist/ | Tecnico | Actualiza paso del checklist |
| POST | pedidos/{id}/evidencia/ | Tecnico | Sube foto antes/despues |
| PATCH | pedidos/{id}/diagnostico/ | Tecnico | Actualiza diagnostico tecnico |
| POST | pedidos/{id}/informe/ | Tecnico | Cierra con informe final + firma |
| POST | pedidos/{id}/dar_de_baja/ | Coordinador | Baja operativa |

### Recomendaciones y dashboard
| Metodo | Path | Descripcion |
|--------|------|-------------|
| GET | recomendaciones/tecnicos/?lat=X&lon=Y | Top 5 tecnicos por score |
| GET | dashboard/kpis/ | Contadores operativos |
| GET | dashboard/pedidos-por-estado/ | Agrupado por status |
| GET | dashboard/pedidos-por-tecnico/ | Carga por tecnico |

## Docs interactivas

Con el servidor corriendo: http://127.0.0.1:8000/api/docs/

## Roles y permisos

| Grupo Django | Rol en API | Puede hacer |
|-------------|------------|-------------|
| (superuser) | admin | Todo |
| coordinadores | coordinador | CRUD completo + dar_de_baja |
| tecnicos | tecnico | Ver pedidos propios + acciones tecnico |
| (ninguno) | usuario | Solo lectura |

Los grupos se crean automaticamente con `seed_demo`.

## Variables de entorno

Ver `.env.example`. En produccion obligatorias:
- `DJANGO_SECRET_KEY` — clave secreta fuerte
- `DJANGO_DEBUG=false`
- `DATABASE_URL` — postgres://user:pass@host/db
- `CORS_ALLOWED_ORIGINS` — origen del frontend

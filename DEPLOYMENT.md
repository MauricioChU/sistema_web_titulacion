# Instrucciones de despliegue (Backend y Frontend)

Este documento recoge los requisitos y pasos recomendados para desplegar correctamente ambos aplicativos: el backend (Django) y el frontend (aplicación web en Node/Vite). Está escrito en español y contiene ejemplos de comandos para entornos Linux/Windows.

## Resumen rápido
- Backend: Django (proyecto en `backend/`), usa virtualenv y `requirements.txt`. Base de datos por defecto en desarrollo: `db.sqlite3`. En producción use PostgreSQL o MySQL. Recomendado: servir con `gunicorn` o `uvicorn` + `nginx` como reverse-proxy.
- Frontend: proyecto Vite/Node en `sistema_web/`. Construir con `npm run build` y servir los archivos estáticos con `nginx` o un CDN.

## Requisitos
- SO: Linux (preferible para servidores) o Windows (para pruebas).
- Python 3.10+ (ver `backend/requirements.txt`).
- Node.js 18+ y `npm` o `pnpm` para el frontend.
- Git configurado y acceso al repositorio remoto.
- En producción: un servidor HTTP (`nginx`) y un process manager (`systemd`) o contenedores (Docker).

## Variables de entorno (ejemplo `.env`)
- `SECRET_KEY` — clave secreta de Django (no usar DEBUG=true en producción).
- `DEBUG=false` — en producción.
- `ALLOWED_HOSTS` — ejemplo: `example.com,www.example.com`.
- `DATABASE_URL` — URL de la base de datos (Postgres/MySQL) si no usa sqlite.
- `MONGO_URI` — si el proyecto usa Mongo para ciertos servicios.
- `MEDIA_ROOT` / `MEDIA_URL` — rutas para archivos subidos.
- `CORS_ALLOWED_ORIGINS` — origenes permitidos para peticiones desde el frontend.

Coloque las variables en un archivo `.env` y carguelas con `django-environ` o exporte en el `systemd` / entorno del contenedor.

## Backend — Pasos de despliegue (Linux)
1. Preparar entorno y dependencias

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configurar variables de entorno
- Crear `.env` con las variables descritas arriba.

3. Base de datos
- Para producción, crear la base en Postgres/MySQL y apuntar `DATABASE_URL`.

4. Migraciones y datos iniciales

```bash
python manage.py migrate
python manage.py loaddata <fixtures>   # si hay fixtures
python manage.py createsuperuser       # crear admin
```

5. Archivos estáticos y media

```bash
python manage.py collectstatic --noinput
# Asegúrese de que nginx tenga acceso a MEDIA_ROOT y STATIC_ROOT
```

6. Ejecutar con Gunicorn / Uvicorn (ejemplo Gunicorn para Django WSGI)

```bash
# Gunicorn (WSGI)
gunicorn config.wsgi:application --workers 3 --bind unix:/run/myproject.sock

# O Uvicorn (ASGI)
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers 4
```

7. Configurar `systemd` (ejemplo)

Crear `/etc/systemd/system/myproject.service` con algo similar a:

```
[Unit]
Description=MyProject Django
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend
EnvironmentFile=/path/to/backend/.env
ExecStart=/path/to/backend/.venv/bin/gunicorn config.wsgi:application --bind unix:/run/myproject.sock

[Install]
WantedBy=multi-user.target
```

8. Nginx reverse proxy (snippet)

```
server {
    listen 80;
    server_name example.com www.example.com;

    location /static/ {
        alias /path/to/backend/static/;
    }

    location /media/ {
        alias /path/to/backend/media/;
    }

    location / {
        proxy_pass http://unix:/run/myproject.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

9. SSL
- Use `certbot` para obtener certificados y configurar HTTPS en nginx.

## Frontend — Pasos de despliegue
1. Instalar dependencias

```bash
cd sistema_web
npm install    # o pnpm install
```

2. Variables de entorno
- Configurar las variables necesarias (ej. `VITE_API_BASE_URL`) antes de `build`.

3. Construir la versión de producción

```bash
npm run build
```

Esto generará una carpeta `dist/` (o equivalente) con los archivos estáticos.

4. Servir los archivos
- Usar `nginx` para servir `dist/`:

```
server {
    listen 80;
    server_name app.example.com;

    root /path/to/sistema_web/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

5. Proxy a backend (si usa rutas API desde el mismo dominio)
- Puede configurar nginx para reenviar `/api/` al backend.

## Contenedores (opcional)
- Recomiendo usar Docker para entornos reproducibles. Crear `Dockerfile` para backend y frontend, y un `docker-compose.yml` que incluya base de datos, redis (si se requiere) y nginx.

## Checklist y pasos de verificación
- [ ] `DEBUG=false` en producción.
- [ ] `SECRET_KEY` seguro y no versionado.
- [ ] Migraciones aplicadas y backups de DB.
- [ ] Permisos correctos para `media/` y `static/`.
- [ ] CORS configurado para el dominio del frontend.
- [ ] Tests básicos ejecutados (`scripts/smoke_backend_api.py` y otros scripts en `backend/scripts/`).
- [ ] Verificar logs (`journalctl -u myproject` y `nginx` logs).

## Comandos útiles del repo (local)
- Ejecutar pruebas/sanity checks en backend (desde la raíz del workspace):

```bash
# Desde workspace folder
cd backend
if (Test-Path .venv/Scripts/python.exe) { .\.venv\Scripts\python.exe scripts\smoke_backend_api.py } else { python scripts/smoke_backend_api.py }
```

## Problemas comunes y soluciones
- Error 500 en producción: revisar `ALLOWED_HOSTS` y `DEBUG=false` + logs de Gunicorn.
- Archivos estáticos no cargan: ejecutar `collectstatic` y revisar `nginx` alias.
- CORS bloquea peticiones: configurar `CORS_ALLOWED_ORIGINS` o `CORS_ALLOW_ALL` según políticas.

---

Si quieres, puedo:
- Generar un `.env.example` con las claves mínimas.
- Crear un `docker-compose.yml` básico para despliegue local.
- Añadir ejemplos de `systemd`/`nginx` personalizados para tu dominio.

Fin del documento.

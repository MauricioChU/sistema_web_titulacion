"""Mapeo global de URLs.

Regla: cada app expone su propio `urls.py` y aqui las prefijamos con `/api/`.
El contrato con el frontend esta resumido en el README del backend.
"""
from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_v1_patterns = [
    # Docs + salud
    path("health/", include("apps.core.urls")),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    # Auth (login, refresh, me)
    path("auth/", include("apps.accounts.urls")),

    # Dominio
    path("", include("apps.clientes.urls")),
    path("", include("apps.cuentas.urls")),
    path("", include("apps.tecnicos.urls")),
    path("", include("apps.inventario.urls")),
    path("", include("apps.pedidos.urls")),
    path("", include("apps.recomendaciones.urls")),
    path("", include("apps.dashboard.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_v1_patterns)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

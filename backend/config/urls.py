from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView as SpectacularSwaggerUI

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerUI.as_view(url_name="schema"), name="swagger-ui"),
    path("api/auth/", include("apps.auth_app.urls")),
    path("api/usuarios/", include("apps.usuarios.urls")),
    path("api/clientes/", include("apps.clientes.urls")),
    path("api/cuentas/", include("apps.cuentas.urls")),
    path("api/tecnicos/", include("apps.tecnicos.urls")),
    path("api/inventario/", include("apps.inventario.urls")),
    path("api/pedidos/", include("apps.pedidos.urls")),
    path("api/notificaciones/", include("apps.notificaciones.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
    path("api/reportes/", include("apps.reportes.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

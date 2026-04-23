from rest_framework.routers import DefaultRouter

from .views import CuentaViewSet

router = DefaultRouter()
router.register("cuentas", CuentaViewSet, basename="cuenta")

urlpatterns = router.urls

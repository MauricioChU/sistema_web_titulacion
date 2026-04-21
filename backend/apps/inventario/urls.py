from rest_framework.routers import DefaultRouter

from .views import ItemInventarioViewSet

router = DefaultRouter()
router.register("inventario", ItemInventarioViewSet, basename="inventario")

urlpatterns = router.urls

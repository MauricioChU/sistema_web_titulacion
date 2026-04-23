from rest_framework.routers import DefaultRouter

from .views import TecnicoViewSet

router = DefaultRouter()
router.register("tecnicos", TecnicoViewSet, basename="tecnico")

urlpatterns = router.urls

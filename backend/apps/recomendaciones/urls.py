from django.urls import path

from .views import RecomendarTecnicoView

urlpatterns = [
    path("recomendaciones/tecnicos/", RecomendarTecnicoView.as_view(), name="recomendaciones-tecnicos"),
]

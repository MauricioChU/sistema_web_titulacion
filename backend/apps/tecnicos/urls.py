from django.urls import path
from .views import TecnicoListView, TecnicoDetailView, TecnicoRecomendarView

urlpatterns = [
    path("", TecnicoListView.as_view(), name="tecnico-list"),
    path("recomendar/", TecnicoRecomendarView.as_view(), name="tecnico-recomendar"),
    path("<str:pk>/", TecnicoDetailView.as_view(), name="tecnico-detail"),
]

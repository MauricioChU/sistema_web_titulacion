from django.urls import path
from .views import UsuarioListView, UsuarioDetailView

urlpatterns = [
    path("", UsuarioListView.as_view(), name="usuario-list"),
    path("<str:pk>/", UsuarioDetailView.as_view(), name="usuario-detail"),
]

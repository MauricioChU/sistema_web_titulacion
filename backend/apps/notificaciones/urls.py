from django.urls import path
from .views import (
    NotificacionListView,
    NotificacionConteoView,
    NotificacionMarcarLeidaView,
    NotificacionMarcarTodasLeidasView,
)

urlpatterns = [
    path("", NotificacionListView.as_view(), name="notificacion-list"),
    path("pendientes/", NotificacionConteoView.as_view(), name="notificacion-pendientes"),
    path("leer-todas/", NotificacionMarcarTodasLeidasView.as_view(), name="notificacion-leer-todas"),
    path("<str:pk>/leer/", NotificacionMarcarLeidaView.as_view(), name="notificacion-leer"),
]

from django.urls import path
from .views import CuentaListView, CuentaDetailView

urlpatterns = [
    path("", CuentaListView.as_view(), name="cuenta-list"),
    path("<str:pk>/", CuentaDetailView.as_view(), name="cuenta-detail"),
]

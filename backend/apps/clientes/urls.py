from django.urls import path
from .views import ClienteListView, ClienteDetailView

urlpatterns = [
    path("", ClienteListView.as_view(), name="cliente-list"),
    path("<str:pk>/", ClienteDetailView.as_view(), name="cliente-detail"),
]

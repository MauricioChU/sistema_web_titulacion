from django.contrib import admin
from .models import Pedido


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "titulo", "cliente", "tecnico_asignado", "fase", "prioridad", "zona", "created_at")
    list_filter = ("fase", "prioridad", "zona")
    search_fields = ("titulo", "cliente__nombre", "tecnico_asignado__nombre")

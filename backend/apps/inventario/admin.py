from django.contrib import admin

from .models import ItemInventario


@admin.register(ItemInventario)
class ItemInventarioAdmin(admin.ModelAdmin):
    list_display = ("sku", "descripcion", "categoria", "stock", "stock_minimo", "almacen", "activo")
    search_fields = ("sku", "descripcion", "categoria")
    list_filter = ("categoria", "almacen", "activo")

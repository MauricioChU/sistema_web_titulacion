from django.contrib import admin
from .models import Cuenta


@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "numero", "tipo", "cliente", "activa")
    list_filter = ("tipo", "activa")
    search_fields = ("nombre", "numero", "cliente__nombre")

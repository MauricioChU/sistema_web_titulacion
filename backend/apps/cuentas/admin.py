from django.contrib import admin

from .models import Cuenta


@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ("numero", "nombre", "cliente", "tipo", "distrito", "activa")
    search_fields = ("numero", "nombre", "cliente__nombre")
    list_filter = ("tipo", "activa")

from django.contrib import admin
from .models import Tecnico


@admin.register(Tecnico)
class TecnicoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "especialidad", "zona", "capacidad_diaria", "activo")
    list_filter = ("especialidad", "zona", "activo")
    search_fields = ("nombre",)

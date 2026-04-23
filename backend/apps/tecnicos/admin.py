from django.contrib import admin

from .models import Tecnico


@admin.register(Tecnico)
class TecnicoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "especialidad", "zona", "capacidad_diaria", "activo")
    search_fields = ("nombre", "especialidad", "zona")
    list_filter = ("activo", "zona", "especialidad")

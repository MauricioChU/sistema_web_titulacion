from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "documento", "telefono", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "documento")

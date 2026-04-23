from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "documento", "correo", "telefono", "activo")
    search_fields = ("nombre", "documento", "correo")
    list_filter = ("activo",)

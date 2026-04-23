from django.contrib import admin

from .models import ChecklistStep, Evidencia, InformeTecnico, Pedido, TecnicoUpdate


class ChecklistStepInline(admin.TabularInline):
    model = ChecklistStep
    extra = 0
    readonly_fields = ("completado_en", "created_at")


class EvidenciaInline(admin.TabularInline):
    model = Evidencia
    extra = 0
    readonly_fields = ("created_at",)


class TecnicoUpdateInline(admin.TabularInline):
    model = TecnicoUpdate
    extra = 0
    readonly_fields = ("created_at",)
    can_delete = False


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "titulo", "cliente", "tecnico_asignado", "fase", "status_operativo", "prioridad", "created_at")
    list_filter = ("fase", "status_operativo", "prioridad")
    search_fields = ("codigo", "titulo", "descripcion")
    readonly_fields = ("codigo", "created_at", "updated_at", "historial")
    inlines = [ChecklistStepInline, EvidenciaInline, TecnicoUpdateInline]
    ordering = ("-created_at",)


@admin.register(InformeTecnico)
class InformeTecnicoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "tecnico", "created_at")
    readonly_fields = ("created_at", "updated_at")

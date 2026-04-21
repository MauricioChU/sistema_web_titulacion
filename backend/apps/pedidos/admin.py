from django.contrib import admin
from .models import ChecklistStep, Evidencia, InformeTecnico, Pedido, TecnicoUpdate


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "titulo",
        "cliente",
        "tecnico_asignado",
        "fase",
        "subfase_tecnica",
        "status_operativo",
        "prioridad",
        "zona",
        "created_at",
    )
    list_filter = ("fase", "subfase_tecnica", "status_operativo", "prioridad", "zona")
    search_fields = ("titulo", "cliente__nombre", "tecnico_asignado__nombre")


@admin.register(TecnicoUpdate)
class TecnicoUpdateAdmin(admin.ModelAdmin):
    list_display = ("id", "pedido", "tecnico", "nuevo_estado", "created_at")
    list_filter = ("nuevo_estado", "created_at")
    search_fields = ("pedido__titulo", "tecnico__nombre", "nota")


@admin.register(ChecklistStep)
class ChecklistStepAdmin(admin.ModelAdmin):
    list_display = ("id", "pedido", "step_id", "completado", "tecnico", "completado_en")
    list_filter = ("step_id", "completado")
    search_fields = ("pedido__titulo", "tecnico__nombre", "nota")


@admin.register(Evidencia)
class EvidenciaAdmin(admin.ModelAdmin):
    list_display = ("id", "pedido", "tecnico", "stage", "source", "created_at")
    list_filter = ("stage", "source", "created_at")
    search_fields = ("pedido__titulo", "tecnico__nombre", "nombre", "descripcion")


@admin.register(InformeTecnico)
class InformeTecnicoAdmin(admin.ModelAdmin):
    list_display = ("id", "pedido", "tecnico", "created_at", "updated_at")
    search_fields = ("pedido__titulo", "tecnico__nombre", "diagnostico_final", "observaciones")

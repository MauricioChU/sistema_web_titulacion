from django.db import models


class Pedido(models.Model):
    class Fase(models.TextChoices):
        CREACION = "creacion", "Creacion"
        PROGRAMACION = "programacion", "Programacion"
        SEGUIMIENTO = "seguimiento", "Seguimiento"
        CIERRE = "cierre", "Cierre"

    class Prioridad(models.TextChoices):
        BAJA = "baja", "Baja"
        MEDIA = "media", "Media"
        ALTA = "alta", "Alta"

    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.PROTECT, related_name="pedidos")
    cuenta = models.ForeignKey("cuentas.Cuenta", on_delete=models.PROTECT, related_name="pedidos", null=True, blank=True)
    tecnico_asignado = models.ForeignKey(
        "tecnicos.Tecnico",
        on_delete=models.SET_NULL,
        related_name="pedidos",
        null=True,
        blank=True,
    )

    titulo = models.CharField(max_length=180)
    descripcion = models.TextField(blank=True)
    tipo_servicio = models.CharField(max_length=80)
    zona = models.CharField(max_length=80)
    prioridad = models.CharField(max_length=10, choices=Prioridad.choices, default=Prioridad.MEDIA)
    fase = models.CharField(max_length=20, choices=Fase.choices, default=Fase.CREACION)

    fecha_programada = models.DateTimeField(null=True, blank=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.titulo} - {self.get_fase_display()}"

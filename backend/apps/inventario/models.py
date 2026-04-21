from django.db import models


class ItemInventario(models.Model):
    sku = models.CharField(max_length=40, unique=True)
    descripcion = models.CharField(max_length=220)
    categoria = models.CharField(max_length=80)
    stock = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=0)
    unidad_medida = models.CharField(max_length=20, default="unidad")
    almacen = models.CharField(max_length=80, default="principal")
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["descripcion"]

    def __str__(self) -> str:
        return f"{self.sku} - {self.descripcion}"

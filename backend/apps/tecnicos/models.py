from django.db import models


class Tecnico(models.Model):
    nombre = models.CharField(max_length=120)
    especialidad = models.CharField(max_length=80)
    zona = models.CharField(max_length=80)
    capacidad_diaria = models.PositiveIntegerField(default=5)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.especialidad})"

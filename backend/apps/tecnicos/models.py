from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Tecnico(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="tecnico_perfil",
        null=True,
        blank=True,
    )
    nombre = models.CharField(max_length=120)
    especialidad = models.CharField(max_length=80)
    zona = models.CharField(max_length=80)
    latitud_base = models.FloatField(validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)])
    longitud_base = models.FloatField(validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)])
    capacidad_diaria = models.PositiveIntegerField(default=5)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.especialidad})"

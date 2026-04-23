from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Cuenta(models.Model):
    """Sede o punto operativo de un cliente.

    Cada cuenta tiene coordenadas que alimentan la recomendacion de tecnico.
    """

    class TipoCuenta(models.TextChoices):
        EMPRESA = "empresa", "Empresa"
        HOGAR = "hogar", "Hogar"
        GOBIERNO = "gobierno", "Gobierno"
        OTRO = "otro", "Otro"

    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE, related_name="cuentas")
    nombre = models.CharField(max_length=150)
    numero = models.CharField(max_length=60)
    direccion = models.CharField(max_length=255, blank=True, default="")
    distrito = models.CharField(max_length=120, blank=True, default="")
    contacto = models.CharField(max_length=120, blank=True, default="")
    telefono = models.CharField(max_length=40, blank=True, default="")
    tipo = models.CharField(max_length=20, choices=TipoCuenta.choices, default=TipoCuenta.OTRO)
    latitud = models.FloatField(validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)])
    longitud = models.FloatField(validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)])
    activa = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre"]
        unique_together = ("cliente", "numero")

    def __str__(self) -> str:
        return f"{self.nombre} ({self.numero})"

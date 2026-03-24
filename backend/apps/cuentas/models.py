from django.db import models


class Cuenta(models.Model):
    class TipoCuenta(models.TextChoices):
        EMPRESA = "empresa", "Empresa"
        HOGAR = "hogar", "Hogar"
        GOBIERNO = "gobierno", "Gobierno"
        OTRO = "otro", "Otro"

    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE, related_name="cuentas")
    nombre = models.CharField(max_length=150)
    numero = models.CharField(max_length=60)
    tipo = models.CharField(max_length=20, choices=TipoCuenta.choices, default=TipoCuenta.OTRO)
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre"]
        unique_together = ("cliente", "numero")

    def __str__(self) -> str:
        return f"{self.nombre} ({self.numero})"

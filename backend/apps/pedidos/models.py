"""Modelos del dominio Pedido.

Un `Pedido` tiene un workflow en 4 fases (`creacion`, `programacion`,
`seguimiento`, `cierre`) y un detalle operativo expresado por `status_operativo`
+ `subfase_tecnica`. Ver `services.py` para las transiciones.

Relaciones auxiliares:
    - `TecnicoUpdate`: bitacora de eventos del tecnico (nota + estado).
    - `ChecklistStep`: pasos checklist fijos durante la ejecucion.
    - `Evidencia`: fotos antes/despues.
    - `InformeTecnico`: entregable final (uno por pedido).
"""
from __future__ import annotations

from django.db import IntegrityError, models, transaction
from django.utils import timezone


class Pedido(models.Model):
    CODE_PREFIX = "A"
    CODE_PADDING = 4

    class Fase(models.TextChoices):
        CREACION = "creacion", "Creacion"
        PROGRAMACION = "programacion", "Programacion"
        SEGUIMIENTO = "seguimiento", "Seguimiento"
        CIERRE = "cierre", "Cierre"

    class Prioridad(models.TextChoices):
        BAJA = "baja", "Baja"
        MEDIA = "media", "Media"
        ALTA = "alta", "Alta"
        CRITICA = "critica", "Critica"

    class StatusOperativo(models.TextChoices):
        POR_CONFIRMAR = "por-confirmar", "Por confirmar"
        CONFIRMADO = "confirmado", "Confirmado"
        EN_LABOR = "en-labor", "En labor"
        CIERRE_TECNICO = "cierre-tecnico", "Cierre tecnico"
        FACTURACION = "facturacion", "Facturacion"
        COMPLETADO = "completado", "Completado"
        DADO_DE_BAJA = "dado-de-baja", "Dado de baja"

    class SubfaseTecnica(models.TextChoices):
        CONFIRMACION = "confirmacion", "Confirmacion"
        EJECUCION = "ejecucion", "Ejecucion"
        EVIDENCIAS = "evidencias", "Evidencias"
        CIERRE_TECNICO = "cierre-tecnico", "Cierre tecnico"
        FACTURACION = "facturacion", "Facturacion"

    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.PROTECT,
        related_name="pedidos",
    )
    cuenta = models.ForeignKey(
        "cuentas.Cuenta",
        on_delete=models.PROTECT,
        related_name="pedidos",
        null=True,
        blank=True,
    )
    tecnico_asignado = models.ForeignKey(
        "tecnicos.Tecnico",
        on_delete=models.SET_NULL,
        related_name="pedidos",
        null=True,
        blank=True,
    )
    codigo = models.CharField(max_length=20, unique=True, db_index=True, editable=False, blank=True)

    titulo = models.CharField(max_length=180)
    descripcion = models.TextField(blank=True)
    tipo_servicio = models.CharField(max_length=80)
    zona = models.CharField(max_length=80)
    prioridad = models.CharField(max_length=10, choices=Prioridad.choices, default=Prioridad.MEDIA)
    fase = models.CharField(max_length=20, choices=Fase.choices, default=Fase.CREACION)
    status_operativo = models.CharField(
        max_length=20,
        choices=StatusOperativo.choices,
        default=StatusOperativo.POR_CONFIRMAR,
    )
    subfase_tecnica = models.CharField(
        max_length=20,
        choices=SubfaseTecnica.choices,
        default=SubfaseTecnica.CONFIRMACION,
    )
    diagnostico_tecnico = models.TextField(blank=True)
    historial = models.JSONField(default=list, blank=True)

    fecha_programada = models.DateTimeField(null=True, blank=True)
    fecha_inicio_labor = models.DateTimeField(null=True, blank=True)
    fecha_fin_labor = models.DateTimeField(null=True, blank=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["fase"]),
            models.Index(fields=["status_operativo"]),
            models.Index(fields=["tecnico_asignado"]),
        ]

    def __str__(self) -> str:
        return f"{self.codigo or 'SIN-CODIGO'} - {self.titulo}"

    # ------------------------------------------------------------------ #
    # Codigo operativo autogenerado (A0001, A0002, ...)                  #
    # ------------------------------------------------------------------ #
    @classmethod
    def _next_codigo(cls) -> str:
        max_counter = 0
        for value in cls.objects.exclude(codigo="").values_list("codigo", flat=True):
            if not isinstance(value, str) or not value.startswith(cls.CODE_PREFIX):
                continue
            number_part = value[len(cls.CODE_PREFIX):]
            if number_part.isdigit():
                max_counter = max(max_counter, int(number_part))
        return f"{cls.CODE_PREFIX}{max_counter + 1:0{cls.CODE_PADDING}d}"

    def save(self, *args, **kwargs):
        if self.codigo:
            return super().save(*args, **kwargs)

        # Reintentar unas pocas veces ante condicion de carrera con codigo.
        for _ in range(5):
            self.codigo = self._next_codigo()
            try:
                with transaction.atomic():
                    return super().save(*args, **kwargs)
            except IntegrityError:
                self.codigo = ""

        raise RuntimeError("No se pudo generar un codigo unico para el pedido.")

    # ------------------------------------------------------------------ #
    # Historial del pedido (lista JSON de eventos)                       #
    # ------------------------------------------------------------------ #
    def agregar_historial(self, evento: str, usuario=None, detalle: str = "") -> None:
        historial = list(self.historial or [])
        historial.append(
            {
                "evento": evento,
                "usuario": getattr(usuario, "username", "sistema"),
                "detalle": detalle or "",
                "timestamp": timezone.now().isoformat(),
            }
        )
        self.historial = historial


class TecnicoUpdate(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="tecnico_updates")
    tecnico = models.ForeignKey(
        "tecnicos.Tecnico",
        on_delete=models.SET_NULL,
        related_name="actualizaciones",
        null=True,
        blank=True,
    )
    nota = models.TextField()
    nuevo_estado = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ChecklistStep(models.Model):
    class StepId(models.TextChoices):
        MATERIALES_LISTOS = "materiales-listos", "Materiales listos"
        LLEGADA_SITIO = "llegada-sitio", "Llegada al sitio"
        INICIO_TRABAJO = "inicio-trabajo", "Inicio de trabajo"
        NOTA_ADICIONAL = "nota-adicional", "Nota adicional"

    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="checklist_steps")
    tecnico = models.ForeignKey(
        "tecnicos.Tecnico",
        on_delete=models.SET_NULL,
        related_name="checklist_steps",
        null=True,
        blank=True,
    )
    step_id = models.CharField(max_length=30, choices=StepId.choices)
    completado = models.BooleanField(default=False)
    nota = models.TextField(blank=True)
    completado_en = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        unique_together = ("pedido", "step_id")


class Evidencia(models.Model):
    class Stage(models.TextChoices):
        ANTES = "antes", "Antes"
        DESPUES = "despues", "Despues"

    class Source(models.TextChoices):
        ARCHIVO = "archivo", "Archivo"
        CAMARA = "camara", "Camara"

    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="evidencias")
    tecnico = models.ForeignKey(
        "tecnicos.Tecnico",
        on_delete=models.SET_NULL,
        related_name="evidencias",
        null=True,
        blank=True,
    )
    nombre = models.CharField(max_length=255, blank=True)
    archivo = models.FileField(upload_to="evidencias/%Y/%m/%d/")
    descripcion = models.TextField()
    stage = models.CharField(max_length=12, choices=Stage.choices)
    source = models.CharField(max_length=12, choices=Source.choices, default=Source.ARCHIVO)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class InformeTecnico(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name="informe_tecnico")
    tecnico = models.ForeignKey(
        "tecnicos.Tecnico",
        on_delete=models.SET_NULL,
        related_name="informes_tecnicos",
        null=True,
        blank=True,
    )
    diagnostico_final = models.TextField()
    responsable_local = models.CharField(max_length=150, blank=True)
    pedido_solicitado = models.CharField(max_length=180, blank=True)
    observaciones = models.TextField()
    recomendaciones = models.TextField()
    firma_cliente = models.FileField(upload_to="firmas/%Y/%m/%d/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

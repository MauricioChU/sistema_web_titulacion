"""Logica operativa del workflow de pedidos.

Aqui vive la toma de decisiones (transiciones de `status_operativo`,
`subfase_tecnica`, `fase`). Las views delegan aca para que queden delgadas
y testeables. Cada funcion hace UNA cosa y retorna el objeto afectado.
"""
from __future__ import annotations

from typing import Iterable

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone

from apps.tecnicos.models import Tecnico

from .models import ChecklistStep, Evidencia, InformeTecnico, Pedido, TecnicoUpdate


class WorkflowError(Exception):
    """Error de negocio (no de permisos ni de validacion de campos)."""


# --------------------------------------------------------------------------- #
# Guardado con historial                                                      #
# --------------------------------------------------------------------------- #
def save_with_history(
    pedido: Pedido,
    *,
    usuario: AbstractUser | None,
    evento: str,
    detalle: str,
    update_fields: Iterable[str],
) -> Pedido:
    pedido.agregar_historial(evento=evento, usuario=usuario, detalle=detalle)
    fields = set(update_fields)
    fields.update({"historial", "updated_at"})
    pedido.save(update_fields=list(fields))
    return pedido


# --------------------------------------------------------------------------- #
# Transiciones invocadas por el tecnico                                       #
# --------------------------------------------------------------------------- #
@transaction.atomic
def confirmar_pedido(pedido: Pedido, *, tecnico: Tecnico, usuario: AbstractUser) -> Pedido:
    """El tecnico confirma que acepta el pedido."""
    if pedido.status_operativo == Pedido.StatusOperativo.DADO_DE_BAJA:
        raise WorkflowError("No se puede confirmar un pedido dado de baja.")

    if pedido.fase == Pedido.Fase.CREACION:
        pedido.fase = Pedido.Fase.PROGRAMACION
    pedido.status_operativo = Pedido.StatusOperativo.CONFIRMADO
    pedido.subfase_tecnica = Pedido.SubfaseTecnica.EJECUCION

    save_with_history(
        pedido,
        usuario=usuario,
        evento="confirmacion_tecnico",
        detalle="El tecnico confirmo la recepcion del pedido.",
        update_fields=["fase", "status_operativo", "subfase_tecnica"],
    )

    TecnicoUpdate.objects.create(
        pedido=pedido,
        tecnico=tecnico,
        nota="Pedido confirmado por tecnico.",
        nuevo_estado=Pedido.StatusOperativo.CONFIRMADO,
    )
    return pedido


@transaction.atomic
def upsert_checklist_step(
    pedido: Pedido,
    *,
    tecnico: Tecnico,
    usuario: AbstractUser,
    step_id: str,
    completado: bool,
    nota: str,
) -> tuple[ChecklistStep, bool]:
    """Crea o actualiza un paso del checklist y avanza la subfase si aplica."""
    valid_steps = {c[0] for c in ChecklistStep.StepId.choices}
    if step_id not in valid_steps:
        raise DjangoValidationError({"step_id": "Paso de checklist no valido."})

    if step_id == ChecklistStep.StepId.NOTA_ADICIONAL and not nota.strip():
        raise DjangoValidationError({"nota": "La nota adicional es obligatoria para este paso."})

    step, created = ChecklistStep.objects.get_or_create(
        pedido=pedido,
        step_id=step_id,
        defaults={"tecnico": tecnico, "completado": completado, "nota": nota},
    )
    if not created:
        step.tecnico = tecnico
        step.completado = completado
        step.nota = nota or step.nota

    step.completado_en = timezone.now() if step.completado else None
    step.save()

    if step.completado and pedido.fecha_inicio_labor is None:
        pedido.fecha_inicio_labor = timezone.now()

    required = {c[0] for c in ChecklistStep.StepId.choices}
    completados = set(pedido.checklist_steps.filter(completado=True).values_list("step_id", flat=True))

    if required.issubset(completados):
        pedido.subfase_tecnica = Pedido.SubfaseTecnica.EVIDENCIAS
    else:
        pedido.subfase_tecnica = Pedido.SubfaseTecnica.EJECUCION

    pedido.status_operativo = Pedido.StatusOperativo.EN_LABOR
    if pedido.fase in {Pedido.Fase.CREACION, Pedido.Fase.PROGRAMACION}:
        pedido.fase = Pedido.Fase.SEGUIMIENTO

    save_with_history(
        pedido,
        usuario=usuario,
        evento="checklist_tecnico",
        detalle=f"Paso actualizado: {step.step_id}",
        update_fields=["fase", "status_operativo", "subfase_tecnica", "fecha_inicio_labor"],
    )

    TecnicoUpdate.objects.create(
        pedido=pedido,
        tecnico=tecnico,
        nota=f"Checklist actualizado: {step.step_id}",
        nuevo_estado=pedido.status_operativo,
    )
    return step, created


@transaction.atomic
def registrar_evidencia(
    pedido: Pedido,
    *,
    tecnico: Tecnico,
    usuario: AbstractUser,
    archivo,
    descripcion: str,
    stage: str,
    source: str,
    nombre: str = "",
) -> Evidencia:
    if stage not in {Evidencia.Stage.ANTES, Evidencia.Stage.DESPUES}:
        raise DjangoValidationError({"stage": "Debes enviar stage=antes o stage=despues."})
    if source not in {Evidencia.Source.ARCHIVO, Evidencia.Source.CAMARA}:
        raise DjangoValidationError({"source": "Debes enviar source=archivo o source=camara."})

    evidencia = Evidencia.objects.create(
        pedido=pedido,
        tecnico=tecnico,
        nombre=nombre or (archivo.name if archivo else ""),
        archivo=archivo,
        descripcion=descripcion,
        stage=stage,
        source=source,
    )

    has_antes = pedido.evidencias.filter(stage=Evidencia.Stage.ANTES).exists()
    has_despues = pedido.evidencias.filter(stage=Evidencia.Stage.DESPUES).exists()
    if has_antes and has_despues:
        pedido.subfase_tecnica = Pedido.SubfaseTecnica.CIERRE_TECNICO
        pedido.status_operativo = Pedido.StatusOperativo.CIERRE_TECNICO
    else:
        pedido.subfase_tecnica = Pedido.SubfaseTecnica.EVIDENCIAS
        pedido.status_operativo = Pedido.StatusOperativo.EN_LABOR

    save_with_history(
        pedido,
        usuario=usuario,
        evento="evidencia_tecnica",
        detalle=f"Evidencia registrada ({stage}): {evidencia.nombre}",
        update_fields=["status_operativo", "subfase_tecnica"],
    )

    TecnicoUpdate.objects.create(
        pedido=pedido,
        tecnico=tecnico,
        nota=f"Evidencia enviada: {evidencia.nombre}",
        nuevo_estado=pedido.status_operativo,
    )
    return evidencia


@transaction.atomic
def actualizar_diagnostico(pedido: Pedido, *, usuario: AbstractUser, diagnostico: str) -> Pedido:
    diagnostico = diagnostico.strip()
    if not diagnostico:
        raise DjangoValidationError({"diagnostico_tecnico": "El diagnostico tecnico no puede estar vacio."})

    pedido.diagnostico_tecnico = diagnostico
    save_with_history(
        pedido,
        usuario=usuario,
        evento="diagnostico_tecnico",
        detalle="Diagnostico tecnico actualizado.",
        update_fields=["diagnostico_tecnico"],
    )
    return pedido


@transaction.atomic
def cerrar_con_informe(
    pedido: Pedido,
    *,
    tecnico: Tecnico,
    usuario: AbstractUser,
    diagnostico_final: str,
    responsable_local: str,
    pedido_solicitado: str,
    observaciones: str,
    recomendaciones: str,
    firma_cliente,
) -> tuple[InformeTecnico, bool]:
    """Cierra el pedido generando/actualizando el informe tecnico final."""
    errors: dict[str, str] = {}
    if not diagnostico_final.strip():
        errors["diagnostico_final"] = "El diagnostico final es obligatorio."
    if not observaciones.strip():
        errors["observaciones"] = "Las observaciones son obligatorias."
    if not recomendaciones.strip():
        errors["recomendaciones"] = "Las recomendaciones son obligatorias."

    informe = getattr(pedido, "informe_tecnico", None)
    creating = informe is None
    if creating and firma_cliente is None:
        errors["firma_cliente"] = "Debes adjuntar la firma del cliente."
    if errors:
        raise DjangoValidationError(errors)

    if creating:
        informe = InformeTecnico(pedido=pedido, tecnico=tecnico)

    informe.tecnico = tecnico
    informe.diagnostico_final = diagnostico_final.strip()
    informe.observaciones = observaciones.strip()
    informe.recomendaciones = recomendaciones.strip()
    informe.responsable_local = responsable_local.strip()
    informe.pedido_solicitado = pedido_solicitado.strip()
    if firma_cliente is not None:
        informe.firma_cliente = firma_cliente
    informe.save()

    now = timezone.now()
    pedido.diagnostico_tecnico = informe.diagnostico_final
    pedido.status_operativo = Pedido.StatusOperativo.COMPLETADO
    pedido.subfase_tecnica = Pedido.SubfaseTecnica.FACTURACION
    pedido.fase = Pedido.Fase.CIERRE
    pedido.fecha_fin_labor = now
    pedido.fecha_cierre = now
    save_with_history(
        pedido,
        usuario=usuario,
        evento="informe_tecnico",
        detalle="Informe tecnico enviado y pedido marcado como completado.",
        update_fields=[
            "diagnostico_tecnico",
            "status_operativo",
            "subfase_tecnica",
            "fase",
            "fecha_fin_labor",
            "fecha_cierre",
        ],
    )

    TecnicoUpdate.objects.create(
        pedido=pedido,
        tecnico=tecnico,
        nota="Informe tecnico enviado. Pedido completado.",
        nuevo_estado=Pedido.StatusOperativo.COMPLETADO,
    )
    return informe, creating


@transaction.atomic
def dar_de_baja(pedido: Pedido, *, usuario: AbstractUser, motivo: str = "", tecnico: Tecnico | None = None) -> Pedido:
    """Baja operativa: marca el pedido como `dado-de-baja` y cierra la fase."""
    if pedido.status_operativo == Pedido.StatusOperativo.DADO_DE_BAJA:
        return pedido

    detalle = "Pedido marcado como dado de baja."
    if motivo.strip():
        detalle = f"{detalle} Motivo: {motivo.strip()}"

    pedido.status_operativo = Pedido.StatusOperativo.DADO_DE_BAJA
    pedido.fase = Pedido.Fase.CIERRE
    if pedido.fecha_cierre is None:
        pedido.fecha_cierre = timezone.now()

    save_with_history(
        pedido,
        usuario=usuario,
        evento="baja_operativa",
        detalle=detalle,
        update_fields=["status_operativo", "fase", "fecha_cierre"],
    )

    TecnicoUpdate.objects.create(
        pedido=pedido,
        tecnico=tecnico,
        nota=motivo.strip() or "Pedido dado de baja por coordinacion.",
        nuevo_estado=Pedido.StatusOperativo.DADO_DE_BAJA,
    )
    return pedido

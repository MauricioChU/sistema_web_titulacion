from dataclasses import dataclass

from apps.pedidos.models import Pedido
from apps.tecnicos.models import Tecnico


FASES_ABIERTAS = [Pedido.Fase.CREACION, Pedido.Fase.PROGRAMACION, Pedido.Fase.SEGUIMIENTO]


@dataclass
class ScoreTecnico:
    tecnico: Tecnico
    score: float
    motivos: list[str]


def _score_tecnico(tecnico: Tecnico, pedido: Pedido) -> ScoreTecnico:
    score = 0.0
    motivos: list[str] = []

    if tecnico.zona.strip().lower() == pedido.zona.strip().lower():
        score += 40
        motivos.append("zona_coincidente")

    if tecnico.especialidad.strip().lower() == pedido.tipo_servicio.strip().lower():
        score += 35
        motivos.append("especialidad_coincidente")

    carga_abierta = tecnico.pedidos.filter(fase__in=FASES_ABIERTAS).count()
    disponibilidad = max(tecnico.capacidad_diaria - carga_abierta, 0)
    score += min(disponibilidad * 5, 25)
    motivos.append(f"disponibilidad_{disponibilidad}")

    return ScoreTecnico(tecnico=tecnico, score=score, motivos=motivos)


def recomendar_tecnico_para_pedido(pedido: Pedido) -> dict:
    tecnicos = Tecnico.objects.filter(activo=True)
    ranking = sorted((_score_tecnico(t, pedido) for t in tecnicos), key=lambda x: x.score, reverse=True)

    sugerido = ranking[0] if ranking else None
    return {
        "pedido_id": pedido.id,
        "sugerido": (
            {
                "id": sugerido.tecnico.id,
                "nombre": sugerido.tecnico.nombre,
                "score": sugerido.score,
                "motivos": sugerido.motivos,
            }
            if sugerido
            else None
        ),
        "ranking": [
            {
                "id": item.tecnico.id,
                "nombre": item.tecnico.nombre,
                "score": item.score,
                "motivos": item.motivos,
            }
            for item in ranking
        ],
    }

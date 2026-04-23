import {
  apiRequest,
  type PaginatedResponse,
  unwrapList,
  withQuery,
} from './http';
import type { ApiRecomendacionTecnico } from './tecnicos';

export interface ApiTecnicoUpdate {
  id: string;
  tecnico_nombre: string;
  nota: string;
  nuevo_estado: string;
  created_at: string;
}

export interface ApiChecklistStep {
  id: string;
  step_id: string;
  completado: boolean;
  nota: string;
  completado_en: string | null;
  created_at: string;
}

export interface ApiEvidencia {
  id: string;
  nombre: string;
  archivo: string;
  descripcion: string;
  stage: 'antes' | 'despues';
  source: 'archivo' | 'camara';
  tecnico_nombre: string;
  created_at: string;
}

export interface ApiInformeTecnico {
  id: string;
  tecnico_nombre: string;
  diagnostico_final: string;
  responsable_local: string;
  pedido_solicitado: string;
  observaciones: string;
  recomendaciones: string;
  firma_cliente: string;
  created_at: string;
  updated_at: string;
}

export interface ApiPedido {
  id: string;
  codigo: string;
  cliente: string;
  cuenta: string | null;
  tecnico_asignado: string | null;
  titulo: string;
  descripcion: string;
  tipo_servicio: string;
  zona: string;
  prioridad: 'baja' | 'media' | 'alta' | 'critica';
  fase: 'creacion' | 'programacion' | 'seguimiento' | 'cierre';
  status_operativo:
    | 'por-confirmar'
    | 'confirmado'
    | 'en-labor'
    | 'cierre-tecnico'
    | 'facturacion'
    | 'completado'
    | 'dado-de-baja';
  subfase_tecnica:
    | 'confirmacion'
    | 'ejecucion'
    | 'evidencias'
    | 'cierre-tecnico'
    | 'facturacion';
  diagnostico_tecnico: string;
  historial: Array<{ evento: string; detalle: string; timestamp: string }>;
  fecha_programada: string | null;
  fecha_inicio_labor: string | null;
  fecha_fin_labor: string | null;
  fecha_cierre: string | null;
  created_at: string;
  updated_at: string;
  cliente_nombre: string;
  cuenta_numero: string;
  cuenta_nombre: string;
  cuenta_direccion: string;
  cuenta_distrito: string;
  cuenta_latitud: number | null;
  cuenta_longitud: number | null;
  tecnico_nombre: string;
  tecnico_updates: ApiTecnicoUpdate[];
  checklist_steps: ApiChecklistStep[];
  evidencias: ApiEvidencia[];
  informe_tecnico: ApiInformeTecnico | null;
}

export interface CreatePedidoPayload {
  cliente: string;
  cuenta?: string | null;
  titulo: string;
  descripcion: string;
  tipo_servicio: string;
  zona: string;
  prioridad: 'baja' | 'media' | 'alta' | 'critica';
  diagnostico_tecnico?: string;
}

export function createPedido(payload: CreatePedidoPayload) {
  return apiRequest<ApiPedido>('/pedidos/', {
    method: 'POST',
    body: payload,
  });
}

export async function listPedidos() {
  const payload = await apiRequest<ApiPedido[] | PaginatedResponse<ApiPedido>>(
    '/pedidos/',
  );
  return unwrapList(payload);
}

export async function listPedidosWithOptions(
  options: { includeBajas?: boolean } = {},
) {
  const path = withQuery('/pedidos/', {
    include_bajas: options.includeBajas,
  });
  const payload = await apiRequest<ApiPedido[] | PaginatedResponse<ApiPedido>>(
    path,
  );
  return unwrapList(payload);
}

export async function listMisAsignados() {
  const payload = await apiRequest<ApiPedido[] | PaginatedResponse<ApiPedido>>(
    '/pedidos/mis-asignados/',
  );
  return unwrapList(payload);
}

export async function fetchPedidoById(pedidoId: string) {
  return apiRequest<ApiPedido>(`/pedidos/${pedidoId}/`);
}

export async function updatePedido(
  pedidoId: string,
  payload: Partial<{
    fase: ApiPedido['fase'];
    prioridad: ApiPedido['prioridad'];
    status_operativo: ApiPedido['status_operativo'];
    diagnostico_tecnico: string;
  }>,
) {
  return apiRequest<ApiPedido>(`/pedidos/${pedidoId}/`, {
    method: 'PATCH',
    body: payload,
  });
}

export async function darBajaPedido(pedidoId: string, motivo = '') {
  return apiRequest<ApiPedido>(`/pedidos/${pedidoId}/dar-baja/`, {
    method: 'POST',
    body: {
      motivo,
    },
  });
}

export async function confirmarTecnico(pedidoId: string) {
  return apiRequest<ApiPedido>(`/pedidos/${pedidoId}/confirmar-tecnico/`, {
    method: 'POST',
    body: {},
  });
}

export function recomendarTecnico(pedidoId: string) {
  return apiRequest<ApiRecomendacionTecnico>(
    `/pedidos/${pedidoId}/recomendar_tecnico/`,
    {
      method: 'POST',
      body: {},
    },
  );
}

export async function upsertChecklist(
  pedidoId: string,
  payload: { stepId: string; completado: boolean; nota?: string },
) {
  return apiRequest<ApiChecklistStep>(`/pedidos/${pedidoId}/checklist/`, {
    method: 'POST',
    body: {
      step_id: payload.stepId,
      completado: payload.completado,
      nota: payload.nota || '',
    },
  });
}

export async function uploadEvidencia(
  pedidoId: string,
  payload: {
    file: File;
    descripcion: string;
    stage: 'antes' | 'despues';
    source: 'archivo' | 'camara';
    nombre?: string;
  },
) {
  const formData = new FormData();
  formData.append('archivo', payload.file);
  formData.append('descripcion', payload.descripcion);
  formData.append('stage', payload.stage);
  formData.append('source', payload.source);
  if (payload.nombre) formData.append('nombre', payload.nombre);

  return apiRequest<ApiEvidencia>(`/pedidos/${pedidoId}/evidencias/`, {
    method: 'POST',
    body: formData,
  });
}

export async function updateDiagnostico(
  pedidoId: string,
  diagnosticoTecnico: string,
) {
  return apiRequest<ApiPedido>(`/pedidos/${pedidoId}/diagnostico/`, {
    method: 'PATCH',
    body: {
      diagnostico_tecnico: diagnosticoTecnico,
    },
  });
}

export async function submitInformeTecnico(
  pedidoId: string,
  payload: {
    diagnosticoFinal: string;
    responsableLocal: string;
    pedidoSolicitado: string;
    observaciones: string;
    recomendaciones: string;
    firmaCliente: File;
  },
) {
  const formData = new FormData();
  formData.append('diagnostico_final', payload.diagnosticoFinal);
  formData.append('responsable_local', payload.responsableLocal);
  formData.append('pedido_solicitado', payload.pedidoSolicitado);
  formData.append('observaciones', payload.observaciones);
  formData.append('recomendaciones', payload.recomendaciones);
  formData.append('firma_cliente', payload.firmaCliente);

  return apiRequest<{ pedido: ApiPedido; informe: ApiInformeTecnico }>(
    `/pedidos/${pedidoId}/informe-tecnico/`,
    {
      method: 'POST',
      body: formData,
    },
  );
}

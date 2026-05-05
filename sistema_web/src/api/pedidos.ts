import { apiRequest, withQuery } from './http';
import { getApiOrigin } from './http';

export interface ApiItemPedido {
  item_id: string;
  sku: string;
  nombre: string;
  cantidad: number;
  precio_unitario: number;
}

export interface ApiChecklistStep {
  step_id: string;
  label: string;
  completado: boolean;
  nota: string;
  completado_en: string | null;
}

export interface ApiEvidencia {
  id: string;
  nombre: string;
  archivo: string;
  descripcion: string;
  stage: 'antes' | 'despues';
  subida_por: string;
  uploaded_at: string;
}

export interface ApiInforme {
  diagnostico_final: string;
  responsable_local: string;
  pedido_solicitado: string;
  observaciones: string;
  recomendaciones: string;
  firma_cliente: string | null;
  created_at: string;
}

export interface ApiHistorialEntry {
  evento: string;
  detalle: string;
  usuario: string;
  at: string;
}

export interface ApiRechazo {
  tecnico_nombre: string;
  motivo: string;
  at: string;
}

export interface ApiPedido {
  id: string;
  codigo: string;
  cliente_id: string;
  cuenta_id: string | null;
  cliente_nombre: string;
  cuenta_nombre: string;
  titulo: string;
  descripcion: string;
  tipo_servicio: string;
  zona: string;
  prioridad: 'baja' | 'media' | 'alta' | 'critica';
  fase: 'creacion' | 'programacion' | 'seguimiento' | 'cierre';
  estado: 'por-confirmar' | 'confirmado' | 'rechazado' | 'en-labor' | 'cierre-tecnico' | 'completado' | 'dado-de-baja';
  tecnico_asignado_id: string | null;
  tecnico_nombre: string | null;
  epps_asignados: ApiItemPedido[];
  materiales_requeridos: ApiItemPedido[];
  materiales_usados: ApiItemPedido[];
  checklist: ApiChecklistStep[];
  evidencias: ApiEvidencia[];
  diagnostico_tecnico: string;
  informe: ApiInforme | null;
  motivo_rechazo: string | null;
  historial_rechazos: ApiRechazo[];
  costo_epps: number;
  costo_materiales: number;
  costo_total: number;
  fecha_programada: string | null;
  fecha_inicio_labor: string | null;
  fecha_fin_labor: string | null;
  fecha_cierre: string | null;
  created_at: string;
  updated_at: string;
  historial: ApiHistorialEntry[];
}

export function evidenciaUrl(path: string): string {
  if (!path) return '';
  if (path.startsWith('http')) return path;
  return `${getApiOrigin()}/media/${path}`;
}

// ── Listado ──────────────────────────────────────────────────────────────────
export function listPedidos(params: Record<string, string | boolean | undefined> = {}): Promise<ApiPedido[]> {
  const url = withQuery('/pedidos/', params as Record<string, string | number | boolean | undefined>);
  return apiRequest<ApiPedido[]>(url);
}

export function getPedido(id: string): Promise<ApiPedido> {
  return apiRequest<ApiPedido>(`/pedidos/${id}/`);
}

// ── CRUD básico ──────────────────────────────────────────────────────────────
export function createPedido(data: Partial<ApiPedido>): Promise<ApiPedido> {
  return apiRequest<ApiPedido>('/pedidos/', { method: 'POST', body: data });
}

export function updatePedido(id: string, data: Partial<ApiPedido>): Promise<ApiPedido> {
  return apiRequest<ApiPedido>(`/pedidos/${id}/`, { method: 'PUT', body: data });
}

export function deletePedido(id: string): Promise<void> {
  return apiRequest<void>(`/pedidos/${id}/`, { method: 'DELETE' });
}

// ── Acciones de coordinador ──────────────────────────────────────────────────
export function asignarTecnico(
  id: string,
  tecnico_id: string,
  epps: ApiItemPedido[] = [],
  materiales_requeridos: ApiItemPedido[] = [],
): Promise<ApiPedido> {
  return apiRequest<ApiPedido>(`/pedidos/${id}/asignar/`, {
    method: 'POST',
    body: { tecnico_id, epps, materiales_requeridos },
  });
}

export function reasignarTecnico(id: string, tecnico_id: string): Promise<ApiPedido> {
  return apiRequest<ApiPedido>(`/pedidos/${id}/reasignar/`, { method: 'POST', body: { tecnico_id } });
}

export function completarPedido(id: string): Promise<ApiPedido> {
  return apiRequest<ApiPedido>(`/pedidos/${id}/completar/`, { method: 'POST' });
}

export function darDeBaja(id: string, motivo: string): Promise<ApiPedido> {
  return apiRequest<ApiPedido>(`/pedidos/${id}/dar-de-baja/`, { method: 'POST', body: { motivo } });
}

// ── Acciones de técnico ──────────────────────────────────────────────────────
export function confirmarPedido(id: string): Promise<ApiPedido> {
  return apiRequest<ApiPedido>(`/pedidos/${id}/confirmar/`, { method: 'POST' });
}

export function rechazarPedido(id: string, motivo: string): Promise<ApiPedido> {
  return apiRequest<ApiPedido>(`/pedidos/${id}/rechazar/`, { method: 'POST', body: { motivo } });
}

export function updateChecklist(id: string, step_id: string, completado: boolean, nota: string): Promise<ApiPedido> {
  return apiRequest<ApiPedido>(`/pedidos/${id}/checklist/`, {
    method: 'POST',
    body: { step_id, completado, nota },
  });
}

export function uploadEvidencia(id: string, file: File, descripcion: string, stage: 'antes' | 'despues'): Promise<ApiPedido> {
  const fd = new FormData();
  fd.append('archivo', file);
  fd.append('descripcion', descripcion);
  fd.append('stage', stage);
  return apiRequest<ApiPedido>(`/pedidos/${id}/evidencia/`, { method: 'POST', body: fd });
}

export function updateDiagnostico(id: string, diagnostico_tecnico: string): Promise<ApiPedido> {
  return apiRequest<ApiPedido>(`/pedidos/${id}/diagnostico/`, {
    method: 'PATCH',
    body: { diagnostico_tecnico },
  });
}

export function registrarMateriales(id: string, materiales: ApiItemPedido[]): Promise<ApiPedido> {
  return apiRequest<ApiPedido>(`/pedidos/${id}/materiales/`, { method: 'POST', body: { materiales } });
}

export function submitInforme(
  id: string,
  data: {
    diagnostico_final: string;
    responsable_local: string;
    pedido_solicitado?: string;
    observaciones: string;
    recomendaciones: string;
    firma_cliente?: File | null;
  },
): Promise<ApiPedido> {
  const fd = new FormData();
  Object.entries(data).forEach(([k, v]) => {
    if (v instanceof File) fd.append(k, v);
    else if (v != null) fd.append(k, String(v));
  });
  return apiRequest<ApiPedido>(`/pedidos/${id}/informe/`, { method: 'POST', body: fd });
}

// ── Reporte PDF ──────────────────────────────────────────────────────────────
export function getPdfUrl(id: string): string {
  return `${getApiOrigin()}/api/reportes/pedido/${id}/pdf/`;
}

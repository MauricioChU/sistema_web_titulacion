import { apiRequest } from './http';

export interface ApiNotificacion {
  id: string;
  tipo: 'pedido_rechazado' | 'pedido_por_confirmar' | 'pedido_completado' | 'stock_bajo' | 'sistema';
  titulo: string;
  mensaje: string;
  para_rol: string | null;
  para_user_id: string | null;
  pedido_id: string | null;
  leida: boolean;
  created_at: string;
}

export interface PendientesResponse {
  no_leidas: number;
  pedidos_pendientes: Array<{ id: string; codigo: string; titulo: string; prioridad: string }>;
  pedidos_rechazados: Array<{ id: string; codigo: string; titulo: string; tecnico_nombre: string; motivo_rechazo: string }>;
}

export function listNotificaciones(soloNoLeidas = false): Promise<ApiNotificacion[]> {
  const url = soloNoLeidas ? '/notificaciones/?no_leidas=true' : '/notificaciones/';
  return apiRequest<ApiNotificacion[]>(url);
}

export function getPendientes(): Promise<PendientesResponse> {
  return apiRequest<PendientesResponse>('/notificaciones/pendientes/');
}

export function marcarLeida(id: string): Promise<void> {
  return apiRequest(`/notificaciones/${id}/leer/`, { method: 'PATCH' });
}

export function marcarTodasLeidas(): Promise<void> {
  return apiRequest('/notificaciones/leer-todas/', { method: 'POST' });
}

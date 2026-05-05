import { apiRequest, withQuery } from './http';

export interface ApiTecnico {
  id: string;
  user_id: string | null;
  nombre: string;
  especialidad: string;
  zona: string;
  telefono: string;
  dni?: string;
  latitud_base: number;
  longitud_base: number;
  activo: boolean;
  pedidos_activos: number;
  created_at: string;
}

export interface ApiRecomendacionItem {
  id: string;
  nombre: string;
  zona: string;
  especialidad?: string;
  telefono?: string;
  dni?: string;
  latitud_base?: number;
  longitud_base?: number;
  score: number;
  score_distancia?: number;
  score_carga?: number;
  score_especialidad?: number;
  distancia_km: number | null;
  pedidos_activos: number;
  specialty_match?: boolean;
  motivos?: string[];
}

export interface ApiRecomendacion {
  pedido_id: string;
  lat_job?: number;
  lon_job?: number;
  sugerido: ApiRecomendacionItem | null;
  ranking: ApiRecomendacionItem[];
}

export function listTecnicos(params: { search?: string; activo?: boolean } = {}): Promise<ApiTecnico[]> {
  return apiRequest<ApiTecnico[]>(withQuery('/tecnicos/', params as Record<string, string | boolean>));
}

export function getTecnico(id: string): Promise<ApiTecnico> {
  return apiRequest<ApiTecnico>(`/tecnicos/${id}/`);
}

export function createTecnico(data: Partial<ApiTecnico>): Promise<ApiTecnico> {
  return apiRequest<ApiTecnico>('/tecnicos/', { method: 'POST', body: data });
}

export function updateTecnico(id: string, data: Partial<ApiTecnico>): Promise<ApiTecnico> {
  return apiRequest<ApiTecnico>(`/tecnicos/${id}/`, { method: 'PUT', body: data });
}

export function deleteTecnico(id: string): Promise<void> {
  return apiRequest<void>(`/tecnicos/${id}/`, { method: 'DELETE' });
}

export function getRecomendacion(pedidoId: string): Promise<ApiRecomendacion> {
  return apiRequest<ApiRecomendacion>(`/tecnicos/recomendar/?pedido_id=${pedidoId}`);
}

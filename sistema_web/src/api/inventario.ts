import { apiRequest, withQuery } from './http';

export interface ApiInventario {
  id: string;
  sku: string;
  nombre: string;
  descripcion: string;
  categoria: 'epp' | 'material' | 'herramienta' | 'otro';
  stock_disponible: number;
  stock_minimo: number;
  unidad: string;
  precio_unitario: number;
  activo: boolean;
  created_at: string;
  updated_at: string;
}

export function listInventario(params: { search?: string; categoria?: string; activo?: boolean } = {}): Promise<ApiInventario[]> {
  return apiRequest<ApiInventario[]>(withQuery('/inventario/', params as Record<string, string | boolean>));
}

export function getInventario(id: string): Promise<ApiInventario> {
  return apiRequest<ApiInventario>(`/inventario/${id}/`);
}

export function createInventario(data: Partial<ApiInventario>): Promise<ApiInventario> {
  return apiRequest<ApiInventario>('/inventario/', { method: 'POST', body: data });
}

export function updateInventario(id: string, data: Partial<ApiInventario>): Promise<ApiInventario> {
  return apiRequest<ApiInventario>(`/inventario/${id}/`, { method: 'PUT', body: data });
}

export function deleteInventario(id: string): Promise<void> {
  return apiRequest<void>(`/inventario/${id}/`, { method: 'DELETE' });
}

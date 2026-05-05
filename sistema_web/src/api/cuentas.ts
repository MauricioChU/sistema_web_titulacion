import { apiRequest, withQuery } from './http';

export interface ApiCuenta {
  id: string;
  cliente_id: string;
  cliente_nombre: string;
  nombre: string;
  numero: string;
  direccion: string;
  distrito: string;
  contacto: string;
  telefono: string;
  tipo: string;
  latitud: number;
  longitud: number;
  activa: boolean;
  created_at: string;
}

export function listCuentas(params: { cliente_id?: string; search?: string } = {}): Promise<ApiCuenta[]> {
  return apiRequest<ApiCuenta[]>(withQuery('/cuentas/', params as Record<string, string>));
}

export function getCuenta(id: string): Promise<ApiCuenta> {
  return apiRequest<ApiCuenta>(`/cuentas/${id}/`);
}

export function createCuenta(data: Partial<ApiCuenta>): Promise<ApiCuenta> {
  return apiRequest<ApiCuenta>('/cuentas/', { method: 'POST', body: data });
}

export function updateCuenta(id: string, data: Partial<ApiCuenta>): Promise<ApiCuenta> {
  return apiRequest<ApiCuenta>(`/cuentas/${id}/`, { method: 'PUT', body: data });
}

export function deleteCuenta(id: string): Promise<void> {
  return apiRequest<void>(`/cuentas/${id}/`, { method: 'DELETE' });
}

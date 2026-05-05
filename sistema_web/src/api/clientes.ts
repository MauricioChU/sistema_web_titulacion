import { apiRequest, withQuery } from './http';

export interface ApiCliente {
  id: string;
  nombre: string;
  ruc: string;
  telefono: string;
  correo: string;
  direccion: string;
  activo: boolean;
  created_at: string;
  updated_at: string;
}

export function listClientes(params: { search?: string } = {}): Promise<ApiCliente[]> {
  return apiRequest<ApiCliente[]>(withQuery('/clientes/', params as Record<string, string>));
}

export function getCliente(id: string): Promise<ApiCliente> {
  return apiRequest<ApiCliente>(`/clientes/${id}/`);
}

export function createCliente(data: Partial<ApiCliente>): Promise<ApiCliente> {
  return apiRequest<ApiCliente>('/clientes/', { method: 'POST', body: data });
}

export function updateCliente(id: string, data: Partial<ApiCliente>): Promise<ApiCliente> {
  return apiRequest<ApiCliente>(`/clientes/${id}/`, { method: 'PUT', body: data });
}

export function deleteCliente(id: string): Promise<void> {
  return apiRequest<void>(`/clientes/${id}/`, { method: 'DELETE' });
}

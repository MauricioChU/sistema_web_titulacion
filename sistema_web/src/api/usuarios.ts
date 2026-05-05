import { apiRequest, withQuery } from './http';

export interface ApiUsuario {
  id: string;
  username: string;
  nombre_completo: string;
  email: string;
  rol: 'admin' | 'coordinador' | 'tecnico';
  privilegio: string | null;
  activo: boolean;
  created_at: string;
  updated_at: string;
}

export function listUsuarios(params: { rol?: string; search?: string } = {}): Promise<ApiUsuario[]> {
  return apiRequest<ApiUsuario[]>(withQuery('/usuarios/', params as Record<string, string>));
}

export function getUsuario(id: string): Promise<ApiUsuario> {
  return apiRequest<ApiUsuario>(`/usuarios/${id}/`);
}

export function createUsuario(data: {
  username: string;
  password: string;
  nombre_completo: string;
  email: string;
  rol: string;
  privilegio?: string | null;
}): Promise<ApiUsuario> {
  return apiRequest<ApiUsuario>('/usuarios/', { method: 'POST', body: data });
}

export function updateUsuario(id: string, data: Partial<ApiUsuario & { password?: string }>): Promise<ApiUsuario> {
  return apiRequest<ApiUsuario>(`/usuarios/${id}/`, { method: 'PUT', body: data });
}

export function deleteUsuario(id: string): Promise<void> {
  return apiRequest<void>(`/usuarios/${id}/`, { method: 'DELETE' });
}

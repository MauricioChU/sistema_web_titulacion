import {
  apiRequest,
  type PaginatedResponse,
  unwrapList,
  withQuery,
} from './http';

export interface ApiCliente {
  id: string;
  nombre: string;
  documento: string;
  telefono: string;
  correo: string;
  direccion: string;
  activo: boolean;
}

export async function listClientes(options: { search?: string } = {}) {
  const path = withQuery('/clientes/', { search: options.search });
  const payload = await apiRequest<
    ApiCliente[] | PaginatedResponse<ApiCliente>
  >(path);
  return unwrapList(payload);
}

export function createCliente(payload: {
  nombre: string;
  documento: string;
  telefono: string;
  correo: string;
  direccion: string;
  activo?: boolean;
}) {
  return apiRequest<ApiCliente>('/clientes/', {
    method: 'POST',
    body: {
      activo: true,
      ...payload,
    },
  });
}

export function updateCliente(
  clienteId: string,
  payload: Partial<{
    nombre: string;
    documento: string;
    telefono: string;
    correo: string;
    direccion: string;
    activo: boolean;
  }>,
) {
  return apiRequest<ApiCliente>(`/clientes/${clienteId}/`, {
    method: 'PATCH',
    body: payload,
  });
}

export function deleteCliente(clienteId: string) {
  return apiRequest<void>(`/clientes/${clienteId}/`, {
    method: 'DELETE',
  });
}

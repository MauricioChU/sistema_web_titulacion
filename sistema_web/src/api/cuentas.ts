import {
  apiRequest,
  type PaginatedResponse,
  unwrapList,
  withQuery,
} from './http';

export interface ApiCuenta {
  id: string;
  cliente: string;
  nombre: string;
  numero: string;
  direccion: string;
  distrito: string;
  contacto: string;
  telefono: string;
  tipo: 'empresa' | 'hogar' | 'gobierno' | 'otro';
  latitud: number;
  longitud: number;
  activa: boolean;
}

export async function listCuentas(
  options: { cliente?: string; search?: string } = {},
) {
  const path = withQuery('/cuentas/', {
    cliente: options.cliente,
    search: options.search,
  });
  const payload = await apiRequest<ApiCuenta[] | PaginatedResponse<ApiCuenta>>(
    path,
  );
  return unwrapList(payload);
}

export function createCuenta(payload: {
  cliente: string;
  nombre: string;
  numero: string;
  latitud: number;
  longitud: number;
  direccion?: string;
  distrito?: string;
  contacto?: string;
  telefono?: string;
  tipo?: 'empresa' | 'hogar' | 'gobierno' | 'otro';
  activa?: boolean;
}) {
  return apiRequest<ApiCuenta>('/cuentas/', {
    method: 'POST',
    body: {
      tipo: 'empresa',
      activa: true,
      ...payload,
    },
  });
}

export function updateCuenta(
  cuentaId: string,
  payload: Partial<{
    cliente: string;
    nombre: string;
    numero: string;
    direccion: string;
    distrito: string;
    contacto: string;
    telefono: string;
    latitud: number;
    longitud: number;
    tipo: 'empresa' | 'hogar' | 'gobierno' | 'otro';
    activa: boolean;
  }>,
) {
  return apiRequest<ApiCuenta>(`/cuentas/${cuentaId}/`, {
    method: 'PATCH',
    body: payload,
  });
}

export function deleteCuenta(cuentaId: string) {
  return apiRequest<void>(`/cuentas/${cuentaId}/`, {
    method: 'DELETE',
  });
}

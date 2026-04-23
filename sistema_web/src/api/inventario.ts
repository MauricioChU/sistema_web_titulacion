import {
  apiRequest,
  type PaginatedResponse,
  unwrapList,
  withQuery,
} from './http';

export interface ApiInventario {
  id: string;
  sku: string;
  descripcion: string;
  categoria: string;
  stock: number;
  stock_minimo: number;
  unidad_medida: string;
  almacen: string;
  activo: boolean;
}

export async function listInventario(
  options: { search?: string; activo?: boolean } = {},
) {
  const path = withQuery('/inventario/', {
    search: options.search,
    activo: options.activo,
  });
  const payload = await apiRequest<
    ApiInventario[] | PaginatedResponse<ApiInventario>
  >(path);
  return unwrapList(payload);
}

export function createInventario(payload: {
  sku: string;
  descripcion: string;
  categoria: string;
  stock: number;
  stock_minimo?: number;
  unidad_medida?: string;
  almacen?: string;
  activo?: boolean;
}) {
  return apiRequest<ApiInventario>('/inventario/', {
    method: 'POST',
    body: {
      stock_minimo: 0,
      unidad_medida: 'unidad',
      almacen: 'principal',
      activo: true,
      ...payload,
    },
  });
}

export function updateInventario(
  itemId: string,
  payload: Partial<{
    sku: string;
    descripcion: string;
    categoria: string;
    stock: number;
    stock_minimo: number;
    unidad_medida: string;
    almacen: string;
    activo: boolean;
  }>,
) {
  return apiRequest<ApiInventario>(`/inventario/${itemId}/`, {
    method: 'PATCH',
    body: payload,
  });
}

export function deleteInventario(itemId: string) {
  return apiRequest<void>(`/inventario/${itemId}/`, {
    method: 'DELETE',
  });
}

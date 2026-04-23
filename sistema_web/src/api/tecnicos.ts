import {
  apiRequest,
  type PaginatedResponse,
  unwrapList,
  withQuery,
} from './http';

export interface ApiTecnico {
  id: string;
  user: string | null;
  nombre: string;
  especialidad: string;
  zona: string;
  latitud_base: number;
  longitud_base: number;
  capacidad_diaria: number;
  activo: boolean;
}

export interface ApiRecomendacionTecnicoItem {
  id: string;
  nombre: string;
  score: number;
  distancia_km: number | null;
  motivos: string[];
}

export interface ApiRecomendacionTecnico {
  pedido_id: string;
  sugerido: ApiRecomendacionTecnicoItem | null;
  ranking: ApiRecomendacionTecnicoItem[];
}

export async function listTecnicos(
  options: { search?: string; activo?: boolean } = {},
) {
  const path = withQuery('/tecnicos/', {
    search: options.search,
    activo: options.activo,
  });
  const payload = await apiRequest<
    ApiTecnico[] | PaginatedResponse<ApiTecnico>
  >(path);
  return unwrapList(payload);
}

export function createTecnico(payload: {
  user?: string | null;
  nombre: string;
  especialidad: string;
  zona: string;
  latitud_base: number;
  longitud_base: number;
  capacidad_diaria?: number;
  activo?: boolean;
}) {
  return apiRequest<ApiTecnico>('/tecnicos/', {
    method: 'POST',
    body: {
      capacidad_diaria: 5,
      activo: true,
      ...payload,
    },
  });
}

export function updateTecnico(
  tecnicoId: string,
  payload: Partial<{
    user: string | null;
    nombre: string;
    especialidad: string;
    zona: string;
    latitud_base: number;
    longitud_base: number;
    capacidad_diaria: number;
    activo: boolean;
  }>,
) {
  return apiRequest<ApiTecnico>(`/tecnicos/${tecnicoId}/`, {
    method: 'PATCH',
    body: payload,
  });
}

export function deleteTecnico(tecnicoId: string) {
  return apiRequest<void>(`/tecnicos/${tecnicoId}/`, {
    method: 'DELETE',
  });
}

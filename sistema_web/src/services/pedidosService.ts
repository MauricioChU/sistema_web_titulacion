import { apiRequest } from './http';

interface PaginatedResponse<T> {
  results: T[];
}

export interface ApiTecnicoUpdate {
  id: string;
  tecnico_nombre: string;
  nota: string;
  nuevo_estado: string;
  created_at: string;
}

export interface ApiChecklistStep {
  id: string;
  step_id: string;
  completado: boolean;
  nota: string;
  completado_en: string | null;
  created_at: string;
}

export interface ApiEvidencia {
  id: string;
  nombre: string;
  archivo: string;
  descripcion: string;
  stage: 'antes' | 'despues';
  source: 'archivo' | 'camara';
  tecnico_nombre: string;
  created_at: string;
}

export interface ApiInformeTecnico {
  id: string;
  tecnico_nombre: string;
  diagnostico_final: string;
  responsable_local: string;
  pedido_solicitado: string;
  observaciones: string;
  recomendaciones: string;
  firma_cliente: string;
  created_at: string;
  updated_at: string;
}

export interface ApiPedido {
  id: string;
  codigo: string;
  cliente: string;
  cuenta: string | null;
  tecnico_asignado: string | null;
  titulo: string;
  descripcion: string;
  tipo_servicio: string;
  zona: string;
  prioridad: 'baja' | 'media' | 'alta' | 'critica';
  fase: 'creacion' | 'programacion' | 'seguimiento' | 'cierre';
  status_operativo:
    | 'por-confirmar'
    | 'confirmado'
    | 'en-labor'
    | 'cierre-tecnico'
    | 'facturacion'
    | 'completado'
    | 'dado-de-baja';
  subfase_tecnica: 'confirmacion' | 'ejecucion' | 'evidencias' | 'cierre-tecnico' | 'facturacion';
  diagnostico_tecnico: string;
  historial: Array<{ evento: string; detalle: string; timestamp: string }>;
  fecha_programada: string | null;
  fecha_inicio_labor: string | null;
  fecha_fin_labor: string | null;
  fecha_cierre: string | null;
  created_at: string;
  updated_at: string;
  cliente_nombre: string;
  cuenta_numero: string;
  cuenta_nombre: string;
  cuenta_direccion: string;
  cuenta_distrito: string;
  cuenta_latitud: number | null;
  cuenta_longitud: number | null;
  tecnico_nombre: string;
  tecnico_updates: ApiTecnicoUpdate[];
  checklist_steps: ApiChecklistStep[];
  evidencias: ApiEvidencia[];
  informe_tecnico: ApiInformeTecnico | null;
}

export interface ApiCliente {
  id: string;
  nombre: string;
  documento: string;
  telefono: string;
  correo: string;
  direccion: string;
  activo: boolean;
}

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

export interface CreatePedidoPayload {
  cliente: string;
  cuenta?: string | null;
  titulo: string;
  descripcion: string;
  tipo_servicio: string;
  zona: string;
  prioridad: 'baja' | 'media' | 'alta' | 'critica';
  diagnostico_tecnico?: string;
}

function unwrapList<T>(payload: T[] | PaginatedResponse<T>) {
  if (Array.isArray(payload)) return payload;
  return payload.results || [];
}

function withQuery(path: string, params: Record<string, string | number | boolean | undefined>) {
  const entries = Object.entries(params).filter(([, value]) => value !== undefined && value !== '');
  if (!entries.length) return path;

  const query = entries
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    .join('&');
  return `${path}?${query}`;
}

export async function listClientes(options: { search?: string } = {}) {
  const path = withQuery('/clientes/', { search: options.search });
  const payload = await apiRequest<ApiCliente[] | PaginatedResponse<ApiCliente>>(path);
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
  }>
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

export async function listCuentas(options: { cliente?: string; search?: string } = {}) {
  const path = withQuery('/cuentas/', { cliente: options.cliente, search: options.search });
  const payload = await apiRequest<ApiCuenta[] | PaginatedResponse<ApiCuenta>>(path);
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
  }>
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

export function createPedido(payload: CreatePedidoPayload) {
  return apiRequest<ApiPedido>('/pedidos/', {
    method: 'POST',
    body: payload,
  });
}

export async function listTecnicos(options: { search?: string; activo?: boolean } = {}) {
  const path = withQuery('/tecnicos/', { search: options.search, activo: options.activo });
  const payload = await apiRequest<ApiTecnico[] | PaginatedResponse<ApiTecnico>>(path);
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
  }>
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

export async function listInventario(options: { search?: string; activo?: boolean } = {}) {
  const path = withQuery('/inventario/', { search: options.search, activo: options.activo });
  const payload = await apiRequest<ApiInventario[] | PaginatedResponse<ApiInventario>>(path);
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
  }>
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

export function recomendarTecnico(pedidoId: string) {
  return apiRequest<ApiRecomendacionTecnico>(`/pedidos/${pedidoId}/recomendar_tecnico/`, {
    method: 'POST',
    body: {},
  });
}

export async function listPedidos() {
  const payload = await apiRequest<ApiPedido[] | PaginatedResponse<ApiPedido>>('/pedidos/');
  return unwrapList(payload);
}

export async function listPedidosWithOptions(options: { includeBajas?: boolean } = {}) {
  const path = withQuery('/pedidos/', {
    include_bajas: options.includeBajas,
  });
  const payload = await apiRequest<ApiPedido[] | PaginatedResponse<ApiPedido>>(path);
  return unwrapList(payload);
}

export async function listMisAsignados() {
  const payload = await apiRequest<ApiPedido[] | PaginatedResponse<ApiPedido>>('/pedidos/mis-asignados/');
  return unwrapList(payload);
}

export async function fetchPedidoById(pedidoId: string) {
  return apiRequest<ApiPedido>(`/pedidos/${pedidoId}/`);
}

export async function updatePedido(
  pedidoId: string,
  payload: Partial<{
    fase: ApiPedido['fase'];
    prioridad: ApiPedido['prioridad'];
    status_operativo: ApiPedido['status_operativo'];
    diagnostico_tecnico: string;
  }>
) {
  return apiRequest<ApiPedido>(`/pedidos/${pedidoId}/`, {
    method: 'PATCH',
    body: payload,
  });
}

export async function darBajaPedido(pedidoId: string, motivo = '') {
  return apiRequest<ApiPedido>(`/pedidos/${pedidoId}/dar-baja/`, {
    method: 'POST',
    body: {
      motivo,
    },
  });
}

export async function confirmarTecnico(pedidoId: string) {
  return apiRequest<ApiPedido>(`/pedidos/${pedidoId}/confirmar-tecnico/`, {
    method: 'POST',
    body: {},
  });
}

export async function upsertChecklist(
  pedidoId: string,
  payload: { stepId: string; completado: boolean; nota?: string }
) {
  return apiRequest<ApiChecklistStep>(`/pedidos/${pedidoId}/checklist/`, {
    method: 'POST',
    body: {
      step_id: payload.stepId,
      completado: payload.completado,
      nota: payload.nota || '',
    },
  });
}

export async function uploadEvidencia(
  pedidoId: string,
  payload: {
    file: File;
    descripcion: string;
    stage: 'antes' | 'despues';
    source: 'archivo' | 'camara';
    nombre?: string;
  }
) {
  const formData = new FormData();
  formData.append('archivo', payload.file);
  formData.append('descripcion', payload.descripcion);
  formData.append('stage', payload.stage);
  formData.append('source', payload.source);
  if (payload.nombre) formData.append('nombre', payload.nombre);

  return apiRequest<ApiEvidencia>(`/pedidos/${pedidoId}/evidencias/`, {
    method: 'POST',
    body: formData,
  });
}

export async function updateDiagnostico(pedidoId: string, diagnosticoTecnico: string) {
  return apiRequest<ApiPedido>(`/pedidos/${pedidoId}/diagnostico/`, {
    method: 'PATCH',
    body: {
      diagnostico_tecnico: diagnosticoTecnico,
    },
  });
}

export async function submitInformeTecnico(
  pedidoId: string,
  payload: {
    diagnosticoFinal: string;
    responsableLocal: string;
    pedidoSolicitado: string;
    observaciones: string;
    recomendaciones: string;
    firmaCliente: File;
  }
) {
  const formData = new FormData();
  formData.append('diagnostico_final', payload.diagnosticoFinal);
  formData.append('responsable_local', payload.responsableLocal);
  formData.append('pedido_solicitado', payload.pedidoSolicitado);
  formData.append('observaciones', payload.observaciones);
  formData.append('recomendaciones', payload.recomendaciones);
  formData.append('firma_cliente', payload.firmaCliente);

  return apiRequest<{ pedido: ApiPedido; informe: ApiInformeTecnico }>(`/pedidos/${pedidoId}/informe-tecnico/`, {
    method: 'POST',
    body: formData,
  });
}

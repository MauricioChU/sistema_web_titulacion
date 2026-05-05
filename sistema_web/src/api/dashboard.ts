import { apiRequest } from './http';

export interface DashboardKpis {
  total_pedidos: number;
  pedidos_activos: number;
  pedidos_completados: number;
  pedidos_dados_baja: number;
  pedidos_rechazados: number;
  sin_tecnico: number;
  criticos_activos: number;
  tecnicos_activos: number;
  tasa_cierre_7d: number;
}

export interface PorEstado { estado: string; total: number; }
export interface PorPrioridad { prioridad: string; total: number; }
export interface PorTecnico { tecnico_id: string; tecnico_nombre: string; pedidos_activos: number; }
export interface Tendencia { fecha: string; creados: number; cerrados: number; }
export interface PedidoMapa {
  id: string; codigo: string; titulo: string; prioridad: string;
  estado: string; cliente: string; tecnico: string;
  lat: number; lon: number; direccion: string;
}
export interface ActividadReciente {
  pedido_id: string; codigo: string; titulo: string; cliente: string;
  evento: string; detalle: string; usuario: string; at: string;
}
export interface AlertaPedido {
  id: string; codigo: string; titulo: string; prioridad: string;
  cliente_nombre: string; zona: string; created_at: string;
}

export interface DashboardData {
  kpis: DashboardKpis;
  por_estado: PorEstado[];
  por_prioridad: PorPrioridad[];
  por_tecnico: PorTecnico[];
  tendencia_7d: Tendencia[];
  alertas: AlertaPedido[];
  actividad_reciente: ActividadReciente[];
  pedidos_mapa: PedidoMapa[];
  costos_mes: { total_epps: number; total_materiales: number; total: number };
}

export function getDashboard(): Promise<DashboardData> {
  return apiRequest<DashboardData>('/dashboard/');
}

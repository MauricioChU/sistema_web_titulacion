export type ViewKey =
  | 'dashboard'
  | 'pedidos'
  | 'pedidos-tecnico'
  | 'base-datos'
  | 'notificaciones'
  | 'usuarios';

export interface MenuItem {
  key: ViewKey;
  label: string;
  icon?: string;
}

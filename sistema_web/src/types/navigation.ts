export type ViewKey =
  | 'dashboard'
  | 'pedidos'
  | 'pedidos-tecnico'
  | 'base-datos';

export interface MenuItem {
  key: ViewKey;
  label: string;
  icon?: string;
}

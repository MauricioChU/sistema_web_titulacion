export type MockViewKey = 'dashboard' | 'pedidos' | 'pedidos-tecnico' | 'base-datos';

export interface MenuItem {
  key: MockViewKey;
  label: string;
}

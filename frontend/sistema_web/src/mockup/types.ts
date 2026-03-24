export type MockViewKey = 'dashboard' | 'pedidos' | 'base-datos';

export interface MenuItem {
  key: MockViewKey;
  label: string;
}

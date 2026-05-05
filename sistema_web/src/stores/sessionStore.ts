export type UserRole = 'admin' | 'coordinador' | 'tecnico';
export type Privilegio = 'supervisor' | null;

export interface SessionUser {
  id: string;
  username: string;
  nombre_completo: string;
  email: string;
  rol: UserRole;
  privilegio: Privilegio;
  avatar?: string | null;
}

const TOKEN_KEY = 'prointel_token';
const USER_KEY  = 'prointel_auth_user';

function store(): Storage | null {
  return typeof window === 'undefined' ? null : window.localStorage;
}

export function getToken(): string {
  return store()?.getItem(TOKEN_KEY) || '';
}

export function setToken(token: string): void {
  store()?.setItem(TOKEN_KEY, token);
}

export function setSessionUser(user: SessionUser): void {
  store()?.setItem(USER_KEY, JSON.stringify(user));
}

export function getSessionUser(): SessionUser | null {
  const raw = store()?.getItem(USER_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw) as SessionUser; } catch { return null; }
}

export function clearSession(): void {
  store()?.removeItem(TOKEN_KEY);
  store()?.removeItem(USER_KEY);
}

// ── Role helpers ──────────────────────────────────────────────────────────────
export function esAdmin(u: SessionUser | null): boolean {
  return u?.rol === 'admin';
}
export function esCoordinador(u: SessionUser | null): boolean {
  return u?.rol === 'coordinador' || u?.rol === 'admin';
}
export function esTecnico(u: SessionUser | null): boolean {
  return u?.rol === 'tecnico';
}
export function esSupervisor(u: SessionUser | null): boolean {
  return u?.rol === 'admin' || (u?.rol === 'coordinador' && u?.privilegio === 'supervisor');
}

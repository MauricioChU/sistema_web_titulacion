export type UserRole = 'admin' | 'coordinador' | 'tecnico' | 'usuario';

export interface SessionUser {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  tecnicoId: number | null;
  tecnicoNombre: string | null;
}

const ACCESS_TOKEN_KEY = 'prointel_access_token';
const REFRESH_TOKEN_KEY = 'prointel_refresh_token';
const USER_KEY = 'prointel_auth_user';

function getStorage(): Storage | null {
  if (typeof window === 'undefined') return null;
  return window.localStorage;
}

export function getAccessToken() {
  return getStorage()?.getItem(ACCESS_TOKEN_KEY) || '';
}

export function getRefreshToken() {
  return getStorage()?.getItem(REFRESH_TOKEN_KEY) || '';
}

export function setTokens(access: string, refresh: string) {
  const storage = getStorage();
  if (!storage) return;
  storage.setItem(ACCESS_TOKEN_KEY, access);
  storage.setItem(REFRESH_TOKEN_KEY, refresh);
}

export function setSessionUser(user: SessionUser) {
  const storage = getStorage();
  if (!storage) return;
  storage.setItem(USER_KEY, JSON.stringify(user));
}

export function getSessionUser(): SessionUser | null {
  const storage = getStorage();
  if (!storage) return null;
  const raw = storage.getItem(USER_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as SessionUser;
  } catch {
    return null;
  }
}

export function clearSession() {
  const storage = getStorage();
  if (!storage) return;
  storage.removeItem(ACCESS_TOKEN_KEY);
  storage.removeItem(REFRESH_TOKEN_KEY);
  storage.removeItem(USER_KEY);
}

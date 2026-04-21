import { apiRequest } from './http';
import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  getSessionUser,
  setSessionUser,
  setTokens,
  type SessionUser,
} from './session';

interface LoginResponse {
  access: string;
  refresh: string;
}

interface RefreshResponse {
  access: string;
  refresh?: string;
}

interface MeResponse {
  id: number;
  username: string;
  email: string;
  role: SessionUser['role'];
  tecnico_id: number | null;
  tecnico_nombre: string | null;
}

function toSessionUser(me: MeResponse): SessionUser {
  return {
    id: me.id,
    username: me.username,
    email: me.email,
    role: me.role,
    tecnicoId: me.tecnico_id,
    tecnicoNombre: me.tecnico_nombre,
  };
}

export async function fetchMe() {
  const me = await apiRequest<MeResponse>('/auth/me/');
  const user = toSessionUser(me);
  setSessionUser(user);
  return user;
}

export async function login(username: string, password: string) {
  const tokens = await apiRequest<LoginResponse>('/auth/login/', {
    method: 'POST',
    auth: false,
    body: { username, password },
  });

  setTokens(tokens.access, tokens.refresh);
  return fetchMe();
}

async function refreshSession() {
  const refresh = getRefreshToken();
  if (!refresh) return false;

  const refreshed = await apiRequest<RefreshResponse>('/auth/refresh/', {
    method: 'POST',
    auth: false,
    body: { refresh },
  });

  if (!refreshed.access) return false;
  setTokens(refreshed.access, refreshed.refresh || refresh);
  return true;
}

export async function restoreSession() {
  const token = getAccessToken();
  const refresh = getRefreshToken();
  if (!token && !refresh) return null;

  try {
    if (refresh) {
      const refreshed = await refreshSession();
      if (!refreshed && !token) {
        clearSession();
        return null;
      }
    }
    return await fetchMe();
  } catch {
    clearSession();
    return null;
  }
}

export function getCachedUser() {
  return getSessionUser();
}

export function logout() {
  clearSession();
}

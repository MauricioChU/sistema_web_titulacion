import {
  clearSession,
  getToken,
  getSessionUser,
  type SessionUser,
  setSessionUser,
  setToken,
} from '../stores/sessionStore';
import { apiRequest } from './http';

interface LoginResponse {
  token: string;
  expires_at: string;
  user: SessionUser;
}

export async function login(username: string, password: string): Promise<SessionUser> {
  const resp = await apiRequest<LoginResponse>('/auth/login/', {
    method: 'POST',
    auth: false,
    body: { username, password },
  });
  setToken(resp.token);
  setSessionUser(resp.user);
  return resp.user;
}

export async function fetchMe(): Promise<SessionUser> {
  const user = await apiRequest<SessionUser>('/auth/me/');
  setSessionUser(user);
  return user;
}

export async function restoreSession(): Promise<SessionUser | null> {
  const token = getToken();
  if (!token) return null;
  try {
    return await fetchMe();
  } catch {
    clearSession();
    return null;
  }
}

export async function logout(): Promise<void> {
  try {
    await apiRequest('/auth/logout/', { method: 'POST' });
  } catch { /* ignore */ }
  clearSession();
}

export function getCachedUser(): SessionUser | null {
  return getSessionUser();
}

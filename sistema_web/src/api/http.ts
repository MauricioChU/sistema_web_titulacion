import { clearSession, getToken } from '../stores/sessionStore';

export interface ApiRequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: BodyInit | Record<string, unknown> | object | null;
  headers?: Record<string, string>;
  auth?: boolean;
}

const DEFAULT_API_BASE = 'http://127.0.0.1:8000/api';

function normalizeBase(b: string) { return b.replace(/\/+$/, ''); }

export function getApiBaseUrl(): string {
  const env = (import.meta as ImportMeta & { env?: { VITE_API_BASE_URL?: string } }).env;
  return normalizeBase(env?.VITE_API_BASE_URL || DEFAULT_API_BASE);
}

export function getApiOrigin(): string {
  try { return new URL(getApiBaseUrl()).origin; } catch { return 'http://127.0.0.1:8000'; }
}

function buildUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) return path;
  const base = getApiBaseUrl();
  return `${base}${path.startsWith('/') ? path : `/${path}`}`;
}

function asErrorMessage(payload: unknown, fallback: string): string {
  if (!payload) return fallback;
  if (typeof payload === 'string') return payload;
  if (typeof payload === 'object') {
    const r = payload as Record<string, unknown>;
    if (typeof r.detail === 'string' && r.detail.trim()) return r.detail;
    const first = Object.values(r)[0];
    if (typeof first === 'string') return first;
    if (Array.isArray(first) && typeof first[0] === 'string') return first[0];
  }
  return fallback;
}

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const method = options.method || 'GET';
  const wantsAuth = options.auth !== false;
  const headers: Record<string, string> = { ...(options.headers || {}) };

  let body: BodyInit | undefined;
  if (options.body == null) {
    body = undefined;
  } else if (options.body instanceof FormData || typeof options.body === 'string') {
    body = options.body;
  } else {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    body = JSON.stringify(options.body);
  }

  if (wantsAuth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(buildUrl(path), { method, headers, body });

  if (response.status === 401 && wantsAuth) {
    clearSession();
    window.location.reload();
    throw new Error('Sesión expirada. Por favor inicia sesión nuevamente.');
  }

  const isJson = response.headers.get('content-type')?.includes('application/json');
  const payload = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    throw new Error(asErrorMessage(payload, 'No se pudo completar la solicitud.'));
  }

  return payload as T;
}

export function withQuery(
  path: string,
  params: Record<string, string | number | boolean | undefined>,
): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== '');
  if (!entries.length) return path;
  return `${path}?${entries.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`).join('&')}`;
}

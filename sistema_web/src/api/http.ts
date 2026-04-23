import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from '../stores/sessionStore';

export interface ApiRequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: BodyInit | Record<string, unknown> | object | null;
  headers?: Record<string, string>;
  auth?: boolean;
}

const DEFAULT_API_BASE = 'http://127.0.0.1:8000/api';

function normalizeBase(base: string) {
  return base.replace(/\/+$/, '');
}

export function getApiBaseUrl() {
  const maybeEnv = (
    import.meta as ImportMeta & { env?: { VITE_API_BASE_URL?: string } }
  ).env;
  const configured = maybeEnv?.VITE_API_BASE_URL || DEFAULT_API_BASE;
  return normalizeBase(configured);
}

export function getApiOrigin() {
  try {
    return new URL(getApiBaseUrl()).origin;
  } catch {
    return 'http://127.0.0.1:8000';
  }
}

function buildUrl(path: string) {
  if (/^https?:\/\//i.test(path)) return path;
  const base = getApiBaseUrl();
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${base}${normalizedPath}`;
}

function asErrorMessage(payload: unknown, fallback: string) {
  if (!payload) return fallback;
  if (typeof payload === 'string') return payload;

  if (typeof payload === 'object') {
    const record = payload as Record<string, unknown>;
    const detail = record.detail;
    if (typeof detail === 'string' && detail.trim()) return detail;

    const firstEntry = Object.values(record)[0];
    if (typeof firstEntry === 'string' && firstEntry.trim()) return firstEntry;
    if (Array.isArray(firstEntry) && typeof firstEntry[0] === 'string')
      return String(firstEntry[0]);
  }

  return fallback;
}

async function refreshAccessToken() {
  const refresh = getRefreshToken();
  if (!refresh) return false;

  const response = await fetch(buildUrl('/auth/refresh/'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh }),
  });

  if (!response.ok) {
    clearSession();
    return false;
  }

  const data = (await response.json()) as { access?: string; refresh?: string };
  if (!data.access) {
    clearSession();
    return false;
  }

  setTokens(data.access, data.refresh || refresh);
  return true;
}

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
  retry = true,
): Promise<T> {
  const method = options.method || 'GET';
  const wantsAuth = options.auth !== false;
  const headers: Record<string, string> = { ...(options.headers || {}) };

  let body: BodyInit | undefined;
  if (options.body == null) {
    body = undefined;
  } else if (
    options.body instanceof FormData ||
    typeof options.body === 'string'
  ) {
    body = options.body;
  } else {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    body = JSON.stringify(options.body);
  }

  if (wantsAuth) {
    const token = getAccessToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }

  const response = await fetch(buildUrl(path), {
    method,
    headers,
    body,
  });

  if (response.status === 401 && wantsAuth && retry) {
    const refreshed = await refreshAccessToken();
    if (refreshed) return apiRequest<T>(path, options, false);
  }

  const isJson = response.headers
    .get('content-type')
    ?.includes('application/json');
  const payload = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    throw new Error(
      asErrorMessage(payload, 'No se pudo completar la solicitud.'),
    );
  }

  return payload as T;
}

export interface PaginatedResponse<T> {
  results: T[];
}

export function unwrapList<T>(payload: T[] | PaginatedResponse<T>) {
  if (Array.isArray(payload)) return payload;
  return payload.results || [];
}

export function withQuery(
  path: string,
  params: Record<string, string | number | boolean | undefined>,
) {
  const entries = Object.entries(params).filter(
    ([, value]) => value !== undefined && value !== '',
  );
  if (!entries.length) return path;

  const query = entries
    .map(
      ([key, value]) =>
        `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`,
    )
    .join('&');
  return `${path}?${query}`;
}

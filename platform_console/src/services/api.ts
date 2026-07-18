import type { ManagementResponse } from '../types/api';

const API_BASE = import.meta.env.VITE_API_BASE || '';

export class ApiError extends Error {
  status: number;
  errors: string[];

  constructor(message: string, status: number, errors: string[] = []) {
    super(message);
    this.status = status;
    this.errors = errors;
  }
}

function getAuthHeaders(): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  const token = localStorage.getItem('access_token');
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<ManagementResponse<T>> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...getAuthHeaders(), ...(options.headers as Record<string, string>) },
  });

  const body = (await response.json()) as ManagementResponse<T>;
  if (!response.ok || !body.success) {
    throw new ApiError(
      body.errors?.[0] || response.statusText,
      response.status,
      body.errors,
    );
  }
  return body;
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await apiFetch<T>(path);
  return res.data;
}

export async function apiPost<T>(path: string, data?: unknown): Promise<T> {
  const res = await apiFetch<T>(path, {
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  });
  return res.data;
}

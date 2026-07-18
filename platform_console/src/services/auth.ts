import { apiPost } from './api';

export interface LoginResponse {
  principal: {
    principal_id: string;
    roles: string[];
    telegram_id: number;
  };
  access_token: string;
  refresh_token: string;
  access_expires_at: string;
  refresh_expires_at: string;
  session_id: string;
}

export interface RefreshResponse {
  access_token: string;
  refresh_token: string;
  access_expires_at: string;
  refresh_expires_at: string;
  session_id: string;
}

export async function login(telegramId: number, loginProof?: string): Promise<LoginResponse> {
  const proof = loginProof || import.meta.env.VITE_IAM_LOGIN_SECRET || '';
  return apiPost<LoginResponse>('/management/identity/login', {
    telegram_id: telegramId,
    login_proof: proof,
  });
}

export async function refresh(refreshToken: string): Promise<RefreshResponse> {
  return apiPost<RefreshResponse>('/management/identity/refresh', {
    refresh_token: refreshToken,
  });
}

export function persistSession(data: LoginResponse): void {
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  localStorage.setItem('session_id', data.session_id);
  localStorage.setItem('actor_telegram_id', String(data.principal.telegram_id));
  localStorage.setItem('roles', JSON.stringify(data.principal.roles));
}

export function clearSession(): void {
  ['access_token', 'refresh_token', 'session_id', 'actor_telegram_id', 'roles'].forEach(
    (k) => localStorage.removeItem(k),
  );
}

export function getStoredRoles(): string[] {
  try {
    return JSON.parse(localStorage.getItem('roles') || '[]');
  } catch {
    return [];
  }
}

export function isAuthenticated(): boolean {
  return Boolean(localStorage.getItem('access_token') && localStorage.getItem('actor_telegram_id'));
}

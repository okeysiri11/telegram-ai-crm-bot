import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import {
  clearSession,
  getStoredRoles,
  isAuthenticated,
  login as apiLogin,
  persistSession,
  refresh,
} from '../services/auth';

interface AuthState {
  isLoggedIn: boolean;
  roles: string[];
  actorTelegramId: number | null;
  login: (telegramId: number) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  hasRole: (minRole: 'readonly' | 'administrator' | 'owner') => boolean;
}

const ROLE_RANK: Record<string, number> = {
  readonly: 0,
  operator: 1,
  manager: 1,
  administrator: 2,
  owner: 3,
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      isLoggedIn: isAuthenticated(),
      roles: getStoredRoles(),
      actorTelegramId: Number(localStorage.getItem('actor_telegram_id')) || null,

      login: async (telegramId: number) => {
        const data = await apiLogin(telegramId);
        persistSession(data);
        set({
          isLoggedIn: true,
          roles: data.principal.roles,
          actorTelegramId: data.principal.telegram_id,
        });
      },

      logout: () => {
        clearSession();
        set({ isLoggedIn: false, roles: [], actorTelegramId: null });
      },

      refreshToken: async () => {
        const rt = localStorage.getItem('refresh_token');
        if (!rt) return;
        const data = await refresh(rt);
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
      },

      hasRole: (minRole) => {
        const roles = get().roles;
        const required = ROLE_RANK[minRole] ?? 0;
        return roles.some((r) => (ROLE_RANK[r] ?? 0) >= required);
      },
    }),
    { name: 'platform-auth', partialize: (s) => ({ actorTelegramId: s.actorTelegramId }) },
  ),
);

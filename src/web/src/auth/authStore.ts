import { create } from "zustand";
import { webConfig } from "@/config/webConfig";
import {
  productionLogin,
  refreshProductionSession,
  validateSessionOnline,
  type AuthSessionPayload,
} from "./identityApi";
import { telemetry } from "@/integrations/telemetry";

export type UserProfile = {
  id: string;
  email: string;
  name: string;
  tenantId: string;
  roleId?: string;
  telegramId?: number;
  identityId?: string;
  sessionId?: string;
  permissions?: string[];
  roles?: string[];
};

type AuthState = {
  user: UserProfile | null;
  accessToken: string | null;
  refreshToken: string | null;
  authMode: "platform_jwt" | "isam" | null;
  accessExpiresAt: string | null;
  mfaReady: boolean;
  login: (email: string, password: string, tenantId: string) => Promise<void>;
  logout: () => void;
  restoreSession: () => void;
  refreshSession: () => Promise<boolean>;
  validateSession: () => Promise<boolean>;
};

const STORAGE_KEY = "ewp_session_v1";

function persist(payload: {
  user: UserProfile;
  accessToken: string;
  refreshToken: string;
  authMode: "platform_jwt" | "isam";
  accessExpiresAt?: string | null;
}) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
}

function fromLogin(session: AuthSessionPayload) {
  const payload = {
    user: session.user,
    accessToken: session.accessToken,
    refreshToken: session.refreshToken,
    authMode: session.authMode,
    accessExpiresAt: session.accessExpiresAt || null,
  };
  persist(payload);
  return payload;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  authMode: null,
  accessExpiresAt: null,
  mfaReady: webConfig.mfaReady,

  login: async (email, password, tenantId) => {
    const session = await productionLogin(email, password, tenantId);
    const payload = fromLogin(session);
    set({
      user: payload.user,
      accessToken: payload.accessToken,
      refreshToken: payload.refreshToken,
      authMode: payload.authMode,
      accessExpiresAt: payload.accessExpiresAt,
    });
    void telemetry.audit(
      "auth_login",
      `${email}; mode=${session.authMode}; tenant=${tenantId}`,
    );
  },

  logout: () => {
    const email = get().user?.email;
    localStorage.removeItem(STORAGE_KEY);
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      authMode: null,
      accessExpiresAt: null,
    });
    if (email) void telemetry.audit("auth_logout", email);
  },

  restoreSession: () => {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw) as {
        user: UserProfile;
        accessToken: string;
        refreshToken: string;
        authMode?: "platform_jwt" | "isam";
        accessExpiresAt?: string;
      };
      // Reject legacy demo tokens — force re-login through production auth
      if (!parsed.accessToken || parsed.accessToken.includes(".demo")) {
        get().logout();
        return;
      }
      set({
        user: parsed.user,
        accessToken: parsed.accessToken,
        refreshToken: parsed.refreshToken,
        authMode: parsed.authMode || (parsed.accessToken.split(".").length === 3 ? "platform_jwt" : "isam"),
        accessExpiresAt: parsed.accessExpiresAt || null,
      });
    } catch {
      get().logout();
    }
  },

  refreshSession: async () => {
    const { refreshToken, authMode, user } = get();
    if (!refreshToken || !authMode) return false;
    try {
      const next = await refreshProductionSession(refreshToken, authMode, user?.identityId);
      const payload = {
        user: user!,
        accessToken: next.accessToken,
        refreshToken: next.refreshToken,
        authMode,
        accessExpiresAt: next.accessExpiresAt || null,
      };
      persist(payload);
      set({
        accessToken: next.accessToken,
        refreshToken: next.refreshToken,
        accessExpiresAt: next.accessExpiresAt || null,
      });
      void telemetry.audit("auth_refresh", authMode);
      return true;
    } catch {
      get().logout();
      return false;
    }
  },

  validateSession: async () => {
    const token = get().accessToken;
    if (!token) return false;
    const ok = await validateSessionOnline(token);
    if (!ok) {
      const refreshed = await get().refreshSession();
      return refreshed;
    }
    return true;
  },
}));

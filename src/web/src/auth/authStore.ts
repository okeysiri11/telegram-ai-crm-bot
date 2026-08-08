import { create } from "zustand";
import { webConfig } from "@/config/webConfig";
import {
  productionLogin,
  productionGoogleLogin,
  productionRegister,
  refreshProductionSession,
  validateSessionOnline,
  type AuthSessionPayload,
} from "./identityApi";
import { telemetry } from "@/integrations/telemetry";
import { wsKey } from "@/multi-role/workspaceSlot";

export type UserProfile = {
  id: string;
  email: string;
  name: string;
  displayName?: string;
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
  loginWithGoogle: (input: {
    email?: string;
    name?: string;
    idToken?: string;
    tenantId: string;
    rememberMe?: boolean;
  }) => Promise<void>;
  register: (email: string, password: string, tenantId: string, name?: string) => Promise<void>;
  logout: () => void;
  restoreSession: () => void;
  refreshSession: () => Promise<boolean>;
  validateSession: () => Promise<boolean>;
};

const STORAGE_KEY_BASE = "ewp_session_v1";
function sessionKey() {
  return wsKey(STORAGE_KEY_BASE);
}

function persist(payload: {
  user: UserProfile;
  accessToken: string;
  refreshToken: string;
  authMode: "platform_jwt" | "isam";
  accessExpiresAt?: string | null;
}) {
  localStorage.setItem(sessionKey(), JSON.stringify(payload));
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
    try {
      localStorage.setItem(wsKey("ews_last_login_at"), new Date().toISOString());
    } catch {
      /* ignore */
    }
    void telemetry.audit(
      "auth_login",
      `${email}; mode=${session.authMode}; tenant=${tenantId}`,
    );
    try {
      const { applyDemoUserSession } = await import("@/multi-role/applyDemoSession");
      applyDemoUserSession(email);
    } catch {
      try {
        const { applyGlobeFlySession } = await import("@/demo/globefly");
        applyGlobeFlySession(email);
      } catch {
        /* ignore */
      }
    }
    try {
      const { logActivity } = await import("@/workspace-engine/activityJournal");
      logActivity({ kind: "login", title: "User signed in", detail: email });
    } catch {
      /* ignore */
    }
  },

  loginWithGoogle: async (input) => {
    const session = await productionGoogleLogin(input);
    const payload = fromLogin(session);
    set({
      user: payload.user,
      accessToken: payload.accessToken,
      refreshToken: payload.refreshToken,
      authMode: payload.authMode,
      accessExpiresAt: payload.accessExpiresAt,
    });
    try {
      localStorage.setItem(wsKey("ews_last_login_at"), new Date().toISOString());
    } catch {
      /* ignore */
    }
    void telemetry.audit(
      "auth_google_login",
      `${payload.user.email}; tenant=${input.tenantId}`,
    );
  },

  register: async (email, password, tenantId, name) => {
    const session = await productionRegister({ email, password, tenantId, name });
    const payload = fromLogin(session);
    set({
      user: payload.user,
      accessToken: payload.accessToken,
      refreshToken: payload.refreshToken,
      authMode: payload.authMode,
      accessExpiresAt: payload.accessExpiresAt,
    });
    void telemetry.audit("auth_register", `${email}; tenant=${tenantId}`);
  },

  logout: () => {
    const email = get().user?.email;
    localStorage.removeItem(sessionKey());
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
    const raw = localStorage.getItem(sessionKey());
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
      // Sprint 40.4 — ISAM opaque sessions live in localStorage; do not wipe on soft refresh failure
      // (prevents login → 401 telemetry → refresh fail → logout → redirect loop).
      if (authMode === "isam" && get().accessToken && get().user) {
        return false;
      }
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

import { create } from "zustand";
import { webConfig } from "@/config/webConfig";

export type UserProfile = {
  id: string;
  email: string;
  name: string;
  tenantId: string;
  roleId?: string;
};

type AuthState = {
  user: UserProfile | null;
  accessToken: string | null;
  refreshToken: string | null;
  mfaReady: boolean;
  login: (email: string, password: string, tenantId: string) => Promise<void>;
  logout: () => void;
  restoreSession: () => void;
};

const STORAGE_KEY = "ewp_session_v1";

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  mfaReady: webConfig.mfaReady,
  login: async (email, _password, tenantId) => {
    const accessToken = `jwt.${btoa(email)}.demo`;
    const refreshToken = `refresh.${btoa(tenantId)}.demo`;
    const lower = email.toLowerCase();
    const roleId =
      lower.startsWith("owner@") || lower.includes("+owner@")
        ? "platform_owner"
        : "role_org_owner";
    const user: UserProfile = {
      id: "usr_demo",
      email,
      name: email.split("@")[0] || "user",
      tenantId,
      roleId,
    };
    const payload = { user, accessToken, refreshToken };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    set(payload);
  },
  logout: () => {
    localStorage.removeItem(STORAGE_KEY);
    set({ user: null, accessToken: null, refreshToken: null });
  },
  restoreSession: () => {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw) as {
        user: UserProfile;
        accessToken: string;
        refreshToken: string;
      };
      set(parsed);
    } catch {
      get().logout();
    }
  },
}));

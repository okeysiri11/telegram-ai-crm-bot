import { create } from "zustand";

const KEY = "ews_last_module_v1";

type LastModuleState = {
  lastRoute: string;
  setLastRoute: (route: string) => void;
};

function read(): string {
  try {
    return localStorage.getItem(KEY) || "/dashboard";
  } catch {
    return "/dashboard";
  }
}

export const useLastModuleStore = create<LastModuleState>((set, get) => ({
  lastRoute: typeof window !== "undefined" ? read() : "/dashboard",
  setLastRoute: (route) => {
    if (get().lastRoute === route) return;
    try {
      localStorage.setItem(KEY, route);
    } catch {
      /* ignore */
    }
    set({ lastRoute: route });
  },
}));

export function rememberModuleRoute(pathname: string) {
  if (!pathname || pathname.startsWith("/login") || pathname.startsWith("/auth")) return;
  useLastModuleStore.getState().setLastRoute(pathname);
}

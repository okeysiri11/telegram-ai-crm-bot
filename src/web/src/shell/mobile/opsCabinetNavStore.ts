import { create } from "zustand";

export type MobileNavLink = {
  id: string;
  label: string;
  href: string;
};

type OpsCabinetNavState = {
  verticalId: string | null;
  title: string;
  roleHint: string;
  items: MobileNavLink[];
  register: (payload: {
    verticalId: string;
    title: string;
    roleHint?: string;
    items: MobileNavLink[];
  }) => void;
  clear: () => void;
};

export const useOpsCabinetNavStore = create<OpsCabinetNavState>((set) => ({
  verticalId: null,
  title: "",
  roleHint: "",
  items: [],
  register: (payload) =>
    set({
      verticalId: payload.verticalId,
      title: payload.title,
      roleHint: payload.roleHint || "",
      items: payload.items,
    }),
  clear: () => set({ verticalId: null, title: "", roleHint: "", items: [] }),
}));

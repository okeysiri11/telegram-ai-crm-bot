import { create } from "zustand";

type MobileChromeState = {
  drawerOpen: boolean;
  moreOpen: boolean;
  favoritesOpen: boolean;
  switcherOpen: boolean;
  setDrawerOpen: (open: boolean) => void;
  setMoreOpen: (open: boolean) => void;
  setFavoritesOpen: (open: boolean) => void;
  setSwitcherOpen: (open: boolean) => void;
  closeAll: () => void;
};

export const useMobileChromeStore = create<MobileChromeState>((set) => ({
  drawerOpen: false,
  moreOpen: false,
  favoritesOpen: false,
  switcherOpen: false,
  setDrawerOpen: (open) => set({ drawerOpen: open, moreOpen: false, favoritesOpen: false, switcherOpen: false }),
  setMoreOpen: (open) => set({ moreOpen: open, drawerOpen: false, favoritesOpen: false, switcherOpen: false }),
  setFavoritesOpen: (open) => set({ favoritesOpen: open, drawerOpen: false, moreOpen: false, switcherOpen: false }),
  setSwitcherOpen: (open) => set({ switcherOpen: open, drawerOpen: false, moreOpen: false, favoritesOpen: false }),
  closeAll: () => set({ drawerOpen: false, moreOpen: false, favoritesOpen: false, switcherOpen: false }),
}));

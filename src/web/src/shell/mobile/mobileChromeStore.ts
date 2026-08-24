import { create } from "zustand";

type MobileChromeState = {
  drawerOpen: boolean;
  moreOpen: boolean;
  favoritesOpen: boolean;
  switcherOpen: boolean;
  createOpen: boolean;
  searchOpen: boolean;
  setDrawerOpen: (open: boolean) => void;
  setMoreOpen: (open: boolean) => void;
  setFavoritesOpen: (open: boolean) => void;
  setSwitcherOpen: (open: boolean) => void;
  setCreateOpen: (open: boolean) => void;
  setSearchOpen: (open: boolean) => void;
  closeAll: () => void;
};

const closed = {
  drawerOpen: false,
  moreOpen: false,
  favoritesOpen: false,
  switcherOpen: false,
  createOpen: false,
  searchOpen: false,
};

export const useMobileChromeStore = create<MobileChromeState>((set) => ({
  ...closed,
  setDrawerOpen: (open) => set({ ...closed, drawerOpen: open }),
  setMoreOpen: (open) => set({ ...closed, moreOpen: open }),
  setFavoritesOpen: (open) => set({ ...closed, favoritesOpen: open }),
  setSwitcherOpen: (open) => set({ ...closed, switcherOpen: open }),
  setCreateOpen: (open) => set({ ...closed, createOpen: open }),
  setSearchOpen: (open) => set({ ...closed, searchOpen: open }),
  closeAll: () => set(closed),
}));

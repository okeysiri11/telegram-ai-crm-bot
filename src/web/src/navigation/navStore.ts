import { create } from "zustand";

type NavState = {
  favorites: string[];
  recent: string[];
  addFavorite: (path: string) => void;
  visit: (path: string) => void;
};

export const useNavStore = create<NavState>((set, get) => ({
  favorites: ["/"],
  recent: ["/"],
  addFavorite: (path) =>
    set((s) => ({
      favorites: s.favorites.includes(path) ? s.favorites : [...s.favorites, path],
    })),
  visit: (path) => {
    if (get().recent[0] === path) return;
    set((s) => ({
      recent: [path, ...s.recent.filter((p) => p !== path)].slice(0, 8),
    }));
  },
}));

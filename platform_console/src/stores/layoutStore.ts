import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { LayoutItem } from '../types/widgets';
import { DEFAULT_LAYOUT } from '../widgets/registry';

interface LayoutState {
  items: LayoutItem[];
  editMode: boolean;
  setItems: (items: LayoutItem[]) => void;
  toggleEditMode: () => void;
  resetLayout: () => void;
}

export const useLayoutStore = create<LayoutState>()(
  persist(
    (set) => ({
      items: DEFAULT_LAYOUT,
      editMode: false,
      setItems: (items) => set({ items }),
      toggleEditMode: () => set((s) => ({ editMode: !s.editMode })),
      resetLayout: () => set({ items: DEFAULT_LAYOUT }),
    }),
    { name: 'dashboard-layout' },
  ),
);

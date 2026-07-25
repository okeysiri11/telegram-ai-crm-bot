import { create } from "zustand";
import type { AcademyMode } from "../types";

type AcademyState = {
  mode: AcademyMode;
  learningByBuilder: Record<string, boolean>;
  setMode: (mode: AcademyMode) => void;
  toggleLearning: (builderId: string, enabled: boolean) => void;
  isLearningEnabled: (builderId: string) => boolean;
};

export const useAcademyStore = create<AcademyState>((set, get) => ({
  mode: "guided_learning",
  learningByBuilder: {},
  setMode: (mode) => set({ mode }),
  toggleLearning: (builderId, enabled) =>
    set((s) => ({
      learningByBuilder: { ...s.learningByBuilder, [builderId]: enabled },
    })),
  isLearningEnabled: (builderId) => get().learningByBuilder[builderId] !== false,
}));

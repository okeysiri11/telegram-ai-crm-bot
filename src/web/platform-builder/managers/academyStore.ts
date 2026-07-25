import { create } from "zustand";
import type { AcademyMode } from "../types";

export type ExperienceLevel = "beginner" | "intermediate" | "advanced" | "expert";

type AcademyState = {
  mode: AcademyMode;
  experienceLevel: ExperienceLevel;
  learningByBuilder: Record<string, boolean>;
  setMode: (mode: AcademyMode) => void;
  setExperienceLevel: (level: ExperienceLevel) => void;
  toggleLearning: (builderId: string, enabled: boolean) => void;
  isLearningEnabled: (builderId: string) => boolean;
};

export const useAcademyStore = create<AcademyState>((set, get) => ({
  mode: "guided_learning",
  experienceLevel: "beginner",
  learningByBuilder: {},
  setMode: (mode) => set({ mode }),
  setExperienceLevel: (experienceLevel) => set({ experienceLevel }),
  toggleLearning: (builderId, enabled) =>
    set((s) => ({
      learningByBuilder: { ...s.learningByBuilder, [builderId]: enabled },
    })),
  isLearningEnabled: (builderId) => get().learningByBuilder[builderId] !== false,
}));

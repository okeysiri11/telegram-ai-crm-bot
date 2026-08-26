import { createContext } from "react";

export type RoomTransitionPhase = "idle" | "leaving" | "entering";

export type RoomTransitionApi = {
  phase: RoomTransitionPhase;
  path: string;
  go: (to: string) => void;
};

export const RoomTransitionContext = createContext<RoomTransitionApi | null>(null);

import type { ReactNode } from "react";
import { RoomTransitionContext } from "./roomTransitionContext";
import { useRoomTransitionState } from "./useRoomTransition";

export function RoomTransitionProvider({ children }: { children: ReactNode }) {
  const api = useRoomTransitionState();
  return <RoomTransitionContext.Provider value={api}>{children}</RoomTransitionContext.Provider>;
}

export { useRoomTransition, useRoomTransitionState } from "./useRoomTransition";

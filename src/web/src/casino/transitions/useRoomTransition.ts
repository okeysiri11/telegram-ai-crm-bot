import { useContext, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { RoomTransitionContext, type RoomTransitionApi, type RoomTransitionPhase } from "./roomTransitionContext";

export type { RoomTransitionApi, RoomTransitionPhase };

export function useRoomTransitionState(): RoomTransitionApi {
  const location = useLocation();
  const navigate = useNavigate();
  const [phase, setPhase] = useState<RoomTransitionPhase>("idle");
  const [from, setFrom] = useState(location.pathname);
  const leaveTimer = useRef<number | null>(null);

  useEffect(() => {
    if (location.pathname === from) return;
    setPhase("entering");
    const t = window.setTimeout(() => {
      setFrom(location.pathname);
      setPhase("idle");
    }, 520);
    return () => window.clearTimeout(t);
  }, [from, location.pathname]);

  useEffect(
    () => () => {
      if (leaveTimer.current != null) window.clearTimeout(leaveTimer.current);
    },
    [],
  );

  function go(to: string) {
    if (to === location.pathname) return;
    setPhase("leaving");
    if (leaveTimer.current != null) window.clearTimeout(leaveTimer.current);
    leaveTimer.current = window.setTimeout(() => navigate(to), 180);
  }

  return { phase, path: location.pathname, go };
}

/** Shared shell veil when a provider is mounted; local fallback for isolated tests. */
export function useRoomTransition(): RoomTransitionApi {
  const ctx = useContext(RoomTransitionContext);
  const local = useRoomTransitionState();
  return ctx ?? local;
}

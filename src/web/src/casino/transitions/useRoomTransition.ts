import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

export function useRoomTransition() {
  const location = useLocation();
  const navigate = useNavigate();
  const [phase, setPhase] = useState<"idle" | "leaving" | "entering">("idle");
  const [from, setFrom] = useState(location.pathname);

  useEffect(() => {
    if (location.pathname === from) return;
    setPhase("entering");
    const t = window.setTimeout(() => {
      setFrom(location.pathname);
      setPhase("idle");
    }, 520);
    return () => window.clearTimeout(t);
  }, [from, location.pathname]);

  function go(to: string) {
    if (to === location.pathname) return;
    setPhase("leaving");
    window.setTimeout(() => navigate(to), 180);
  }

  return { phase, path: location.pathname, go };
}

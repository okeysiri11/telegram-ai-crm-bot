import { useEffect, useState } from "react";

/** Matches Tailwind `md` (768px): mobile chrome is max-width 767px. */
export const MOBILE_MAX_WIDTH = 767;

function readMobile(maxWidth: number): boolean {
  if (typeof window === "undefined") return false;
  return window.innerWidth <= maxWidth;
}

export function useIsMobile(maxWidth = MOBILE_MAX_WIDTH): boolean {
  const [mobile, setMobile] = useState(() => readMobile(maxWidth));

  useEffect(() => {
    const sync = () => setMobile(readMobile(maxWidth));
    sync();
    if (typeof window.matchMedia !== "function") {
      window.addEventListener("resize", sync);
      return () => window.removeEventListener("resize", sync);
    }
    const mq = window.matchMedia(`(max-width: ${maxWidth}px)`);
    mq.addEventListener?.("change", sync);
    return () => mq.removeEventListener?.("change", sync);
  }, [maxWidth]);

  return mobile;
}

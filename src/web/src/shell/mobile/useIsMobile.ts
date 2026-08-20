import { useEffect, useState } from "react";

/** Matches Tailwind `md` (768px): mobile chrome is max-width 767px. */
export const MOBILE_MAX_WIDTH = 767;

export function useIsMobile(maxWidth = MOBILE_MAX_WIDTH): boolean {
  const [mobile, setMobile] = useState(() =>
    typeof window !== "undefined" ? window.innerWidth <= maxWidth : false,
  );

  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${maxWidth}px)`);
    const sync = () => setMobile(mq.matches);
    sync();
    mq.addEventListener("change", sync);
    return () => mq.removeEventListener("change", sync);
  }, [maxWidth]);

  return mobile;
}

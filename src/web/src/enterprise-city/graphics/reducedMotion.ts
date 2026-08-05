/**
 * Enterprise City Graphics Engine — Reduced Motion.
 * Sprint CG-3. Combines the platform's real, already-established reduced-motion signal
 * (`accessibilityManager` sets `data-reduced-motion` on `<html>` — see
 * `design-system/accessibility/index.ts`, read the same way `src/ui/Charts.tsx` already reads it)
 * with the OS-level `prefers-reduced-motion` media query, so the Graphics Engine honors either
 * source rather than inventing a third, City-specific setting.
 */

export function isReducedMotionActive(graphicsSettingsFlag = false): boolean {
  if (graphicsSettingsFlag) return true;
  if (typeof document !== "undefined") {
    if (document.documentElement.getAttribute("data-reduced-motion") === "true") return true;
  }
  if (typeof window !== "undefined" && typeof window.matchMedia === "function") {
    try {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return true;
    } catch {
      /* matchMedia unsupported in this environment — fall through */
    }
  }
  return false;
}

/** Subscribe to changes in the OS-level reduced-motion preference. Returns an unsubscribe function. */
export function subscribeReducedMotionPreference(onChange: (matches: boolean) => void): () => void {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return () => {};
  let mql: MediaQueryList;
  try {
    mql = window.matchMedia("(prefers-reduced-motion: reduce)");
  } catch {
    return () => {};
  }
  const handler = () => onChange(mql.matches);
  mql.addEventListener?.("change", handler);
  return () => mql.removeEventListener?.("change", handler);
}

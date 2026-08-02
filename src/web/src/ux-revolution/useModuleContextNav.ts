/**
 * Sprint 33.1 — Resolve context nav from current location + mode.
 */

import { useMemo } from "react";
import { useLocation } from "react-router-dom";
import { useExperienceModeStore } from "./experienceModeStore";
import { resolveModuleContext, type ModuleContext } from "./moduleContextNav";

export function useModuleContextNav(): ModuleContext | null {
  const { pathname, search } = useLocation();
  const mode = useExperienceModeStore((s) => s.mode);
  return useMemo(
    () =>
      resolveModuleContext(`${pathname}${search}`, {
        pro: mode === "pro",
      }),
    [pathname, search, mode],
  );
}

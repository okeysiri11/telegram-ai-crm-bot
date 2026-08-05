import { createContext, useContext } from "react";
import type { useLiveRuntime } from "../hooks/useLiveRuntime";

export type RuntimeContextValue = ReturnType<typeof useLiveRuntime>;

export const RuntimeContext = createContext<RuntimeContextValue | null>(null);

export function useRuntime() {
  const ctx = useContext(RuntimeContext);
  if (!ctx) throw new Error("useRuntime must be used within ControlShell");
  return ctx;
}

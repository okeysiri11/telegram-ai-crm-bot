import { useEffect, useState } from "react";

export type PerformanceTier = "HIGH" | "MEDIUM" | "LOW";

export type PerformanceInput = {
  width: number;
  dpr: number;
  cores: number;
  reducedMotion: boolean;
  touch?: boolean;
};

export function resolvePerformanceTier(input: PerformanceInput): PerformanceTier {
  if (input.reducedMotion) return "LOW";
  const mobile = Boolean(input.touch) || input.width <= 430;
  if (mobile && (input.dpr >= 3 || input.cores <= 4 || input.width <= 360)) return "LOW";
  if (mobile) return "MEDIUM";
  if (input.width < 1366 || input.cores <= 4 || input.dpr >= 2.5) return "MEDIUM";
  if (input.width >= 1440 && input.cores >= 6 && input.dpr <= 2) return "HIGH";
  return "MEDIUM";
}

export function readPerformanceInput(): PerformanceInput {
  if (typeof window === "undefined") {
    return { width: 1280, dpr: 1, cores: 8, reducedMotion: false, touch: false };
  }
  return {
    width: window.innerWidth,
    dpr: window.devicePixelRatio || 1,
    cores: navigator.hardwareConcurrency || 4,
    reducedMotion: window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches ?? false,
    touch: window.matchMedia?.("(pointer: coarse)")?.matches ?? false,
  };
}

export function usePerformanceTier(): PerformanceTier {
  const [tier, setTier] = useState<PerformanceTier>(() => resolvePerformanceTier(readPerformanceInput()));

  useEffect(() => {
    const apply = () => setTier(resolvePerformanceTier(readPerformanceInput()));
    apply();
    window.addEventListener("resize", apply);
    const media = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    media?.addEventListener?.("change", apply);
    return () => {
      window.removeEventListener("resize", apply);
      media?.removeEventListener?.("change", apply);
    };
  }, []);

  return tier;
}

export const accessibilityManager = {
  standard: "WCAG AA",
  features: [
    "keyboard_navigation",
    "screen_reader",
    "focus_management",
    "high_contrast",
    "reduced_motion",
  ] as const,
  focusRingClass: "eds-focus-ring",
  highContrastAttr: "data-contrast",
  reducedMotionQuery: "(prefers-reduced-motion: reduce)",
  apply({ highContrast, reduceMotion }: { highContrast?: boolean; reduceMotion?: boolean }) {
    if (typeof document === "undefined") return;
    document.documentElement.setAttribute("data-contrast", highContrast ? "high" : "normal");
    document.documentElement.setAttribute("data-reduced-motion", reduceMotion ? "true" : "false");
  },
};

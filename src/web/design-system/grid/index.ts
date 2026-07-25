export const gridSystem = {
  columns: 12,
  gutters: { mobile: "1rem", tablet: "1.25rem", desktop: "1.5rem" },
  containers: {
    fluid: "100%",
    fixed: { sm: "640px", md: "768px", lg: "1024px", xl: "1280px" },
  },
  variants: {
    responsive: "eds-grid eds-grid--responsive",
    dashboard: "eds-grid eds-grid--dashboard",
    workspace: "eds-grid eds-grid--workspace",
  },
} as const;

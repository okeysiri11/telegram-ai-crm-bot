export type ThemeId = "light" | "dark" | "corporate" | "custom";

export type BrandOverrides = {
  primary?: string;
  primarySoft?: string;
  font?: string;
};

export function applyTheme(theme: ThemeId, brand?: BrandOverrides) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  root.setAttribute("data-theme", theme === "custom" ? "light" : theme);
  root.setAttribute("data-brand", theme === "corporate" || theme === "custom" ? theme : "default");
  if (brand?.primary) root.style.setProperty("--eds-primary", brand.primary);
  if (brand?.primarySoft) root.style.setProperty("--eds-primary-soft", brand.primarySoft);
  if (brand?.font) root.style.setProperty("--eds-font-sans", brand.font);
}

export const themeEngine = {
  themes: ["light", "dark", "corporate", "custom"] as const,
  apply: applyTheme,
};

/** Design Tokens — single source of truth for Enterprise Design System. */

export const colors = {
  primary: { DEFAULT: "#0f6a5a", soft: "#d8efe9", hover: "#0c5649", active: "#0a4a3f", focus: "#0f6a5a" },
  secondary: { DEFAULT: "#1f3a5f", soft: "#e4ebf5", hover: "#18304f", active: "#14283f" },
  accent: { DEFAULT: "#1f3a5f", soft: "#e4ebf5" },
  success: { DEFAULT: "#027a48", soft: "#d1fadf" },
  warning: { DEFAULT: "#b54708", soft: "#fef0c7" },
  danger: { DEFAULT: "#b42318", soft: "#fee4e2" },
  critical: { DEFAULT: "#b42318", soft: "#fee4e2" },
  info: { DEFAULT: "#026aa2", soft: "#e0f2fe" },
  neutral: {
    0: "#ffffff",
    50: "#f8fafc",
    100: "#f1f5f9",
    200: "#e2e8f0",
    300: "#cbd5e1",
    400: "#94a3b8",
    500: "#64748b",
    600: "#475569",
    700: "#334155",
    800: "#1e293b",
    900: "#0f172a",
  },
  background: { light: "#f4f6f8", dark: "#0b1220", corporate: "#f0f3f7" },
  surface: { light: "#ffffff", dark: "#121a2a", corporate: "#ffffff" },
  border: { light: "#d7dee7", dark: "#243247", corporate: "#c9d3df" },
  text: { light: "#142033", dark: "#e8eef7", mutedLight: "#5b6b7c", mutedDark: "#9aa8b8", disabled: "#94a3b8" },
} as const;

export const fonts = {
  sans: '"IBM Plex Sans", "Segoe UI", sans-serif',
  display: '"IBM Plex Sans", "Segoe UI", sans-serif',
  mono: '"IBM Plex Mono", ui-monospace, monospace',
} as const;

export const fontSizes = {
  displayXl: "3rem",
  displayL: "2.25rem",
  h1: "1.875rem",
  h2: "1.5rem",
  h3: "1.25rem",
  h4: "1.125rem",
  bodyLarge: "1.125rem",
  body: "1rem",
  small: "0.875rem",
  caption: "0.75rem",
  label: "0.8125rem",
  button: "0.875rem",
} as const;

export const fontWeights = {
  regular: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
} as const;

export const radii = {
  none: "0",
  sm: "0.25rem",
  md: "0.375rem",
  lg: "0.5rem",
  xl: "0.75rem",
  full: "9999px",
} as const;

export const shadows = {
  none: "none",
  sm: "0 1px 2px rgba(15, 23, 42, 0.06)",
  md: "0 4px 12px rgba(15, 23, 42, 0.08)",
  lg: "0 12px 28px rgba(15, 23, 42, 0.12)",
  focus: "0 0 0 3px rgba(15, 106, 90, 0.35)",
} as const;

export const spacing = {
  0: "0",
  1: "0.25rem",
  2: "0.5rem",
  3: "0.75rem",
  4: "1rem",
  5: "1.25rem",
  6: "1.5rem",
  8: "2rem",
  10: "2.5rem",
  12: "3rem",
  16: "4rem",
} as const;

export const zIndex = {
  base: 0,
  dropdown: 20,
  sticky: 30,
  drawer: 40,
  modal: 50,
  toast: 60,
  tooltip: 70,
} as const;

export const breakpoints = {
  mobile: 0,
  tablet: 768,
  laptop: 1024,
  desktop: 1280,
} as const;

export const motion = {
  instant: "80ms",
  fast: "120ms",
  normal: "200ms",
  slow: "320ms",
  settle: "400ms",
  easing: "cubic-bezier(0.2, 0.8, 0.2, 1)",
  easeOut: "cubic-bezier(0.16, 1, 0.3, 1)",
  easeIn: "cubic-bezier(0.4, 0, 1, 1)",
  easeEmphasized: "cubic-bezier(0.2, 0, 0, 1)",
  stagger: "40ms",
} as const;

export const opacity = {
  disabled: 0.5,
  muted: 0.7,
  overlay: 0.4,
  full: 1,
} as const;

export const tokens = {
  colors,
  fonts,
  fontSizes,
  fontWeights,
  radii,
  shadows,
  spacing,
  zIndex,
  breakpoints,
  motion,
  opacity,
} as const;

export type DesignTokens = typeof tokens;

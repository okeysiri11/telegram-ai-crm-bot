import { colors } from "../tokens";

export const colorSystem = {
  primary: colors.primary,
  secondary: colors.secondary,
  success: colors.success,
  warning: colors.warning,
  danger: colors.danger,
  info: colors.info,
  neutral: colors.neutral,
  background: colors.background,
  surface: colors.surface,
  border: colors.border,
  text: colors.text,
  disabled: colors.text.disabled,
  hover: { primary: colors.primary.hover, secondary: colors.secondary.hover },
  active: { primary: colors.primary.active, secondary: colors.secondary.active },
  focus: { ring: colors.primary.focus },
} as const;

export type ColorSystem = typeof colorSystem;

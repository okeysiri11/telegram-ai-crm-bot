import { spacing } from "../tokens";

export const spacingSystem = {
  ...spacing,
  scale: [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16] as const,
} as const;

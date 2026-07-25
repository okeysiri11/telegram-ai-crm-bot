import { fontSizes, fonts, fontWeights } from "../tokens";

export const typography = {
  displayXl: { size: fontSizes.displayXl, weight: fontWeights.bold, family: fonts.display, lineHeight: 1.15 },
  displayL: { size: fontSizes.displayL, weight: fontWeights.bold, family: fonts.display, lineHeight: 1.2 },
  heading1: { size: fontSizes.h1, weight: fontWeights.semibold, family: fonts.display, lineHeight: 1.25 },
  heading2: { size: fontSizes.h2, weight: fontWeights.semibold, family: fonts.display, lineHeight: 1.3 },
  heading3: { size: fontSizes.h3, weight: fontWeights.semibold, family: fonts.sans, lineHeight: 1.35 },
  heading4: { size: fontSizes.h4, weight: fontWeights.medium, family: fonts.sans, lineHeight: 1.4 },
  bodyLarge: { size: fontSizes.bodyLarge, weight: fontWeights.regular, family: fonts.sans, lineHeight: 1.5 },
  body: { size: fontSizes.body, weight: fontWeights.regular, family: fonts.sans, lineHeight: 1.5 },
  small: { size: fontSizes.small, weight: fontWeights.regular, family: fonts.sans, lineHeight: 1.45 },
  caption: { size: fontSizes.caption, weight: fontWeights.regular, family: fonts.sans, lineHeight: 1.4 },
  label: { size: fontSizes.label, weight: fontWeights.medium, family: fonts.sans, lineHeight: 1.3 },
  buttonText: { size: fontSizes.button, weight: fontWeights.medium, family: fonts.sans, lineHeight: 1.2 },
} as const;

export type TypographyScale = keyof typeof typography;

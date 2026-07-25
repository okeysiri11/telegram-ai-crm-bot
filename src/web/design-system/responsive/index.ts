import { breakpoints } from "../tokens";

export type Viewport = "mobile" | "tablet" | "laptop" | "desktop";

export const responsiveEngine = {
  breakpoints,
  viewports: ["mobile", "tablet", "laptop", "desktop"] as const,
  media: {
    mobile: `(min-width: ${breakpoints.mobile}px)`,
    tablet: `(min-width: ${breakpoints.tablet}px)`,
    laptop: `(min-width: ${breakpoints.laptop}px)`,
    desktop: `(min-width: ${breakpoints.desktop}px)`,
  },
  resolve(width: number): Viewport {
    if (width >= breakpoints.desktop) return "desktop";
    if (width >= breakpoints.laptop) return "laptop";
    if (width >= breakpoints.tablet) return "tablet";
    return "mobile";
  },
};

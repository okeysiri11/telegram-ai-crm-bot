import { componentCatalog } from "../catalog";
import { tokens } from "../tokens";
import { themeEngine } from "../theme";
import { accessibilityManager } from "../accessibility";
import { responsiveEngine } from "../responsive";

export function generateDesignDocumentation() {
  return {
    componentGuide: componentCatalog.map((c) => ({
      name: c.name,
      api: c.api,
      examples: c.examples,
      usageRules: c.usageRules,
    })),
    uiGuidelines: [
      "Use design tokens only — no hard-coded colors/spacing in modules",
      "Prefer composition over one-off styles",
      "One primary action per view",
      "Support keyboard and screen readers by default",
    ],
    designTokensReference: tokens,
    themeDocumentation: {
      themes: themeEngine.themes,
      branding: ["primary", "primarySoft", "font"],
    },
    accessibilityGuide: {
      standard: accessibilityManager.standard,
      features: accessibilityManager.features,
    },
    responsiveGuide: {
      viewports: responsiveEngine.viewports,
      breakpoints: responsiveEngine.breakpoints,
    },
  };
}

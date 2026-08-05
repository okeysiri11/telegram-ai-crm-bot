import { describe, expect, it } from "vitest";
import {
  DESIGN_SYSTEM_VERSION,
  ENTERPRISE_DESIGN_LANGUAGE,
  MOTION_DESIGN_LANGUAGE,
  animationEngine,
  componentCatalog,
  generateDesignDocumentation,
  iconLibrary,
  responsiveEngine,
  tokens,
  typography,
} from "../../design-system";

describe("Enterprise Design System", () => {
  it("exposes version and core tokens", () => {
    expect(DESIGN_SYSTEM_VERSION).toBe("9.4.0");
    expect(ENTERPRISE_DESIGN_LANGUAGE).toBe("1.0");
    expect(tokens.colors.primary.DEFAULT).toBeTruthy();
    expect(tokens.colors.accent.DEFAULT).toBeTruthy();
    expect(tokens.breakpoints.desktop).toBe(1280);
    expect(typography.displayXl.size).toBeTruthy();
  });

  it("covers catalog, icons, animation, responsive", () => {
    expect(componentCatalog.length).toBeGreaterThanOrEqual(12);
    expect(Object.keys(iconLibrary)).toContain("workflow");
    expect(animationEngine.presets.skeleton).toBe("edm-skeleton");
    expect(animationEngine.presets.pageTransition).toBe("edm-page");
    expect(animationEngine.presets.aiSuggest).toBe("edm-ai-suggest");
    expect(responsiveEngine.resolve(1300)).toBe("desktop");
  });

  it("exposes Motion Design Language version", () => {
    expect(MOTION_DESIGN_LANGUAGE).toBe("1.0");
    expect(tokens.motion.instant).toBe("80ms");
    expect(tokens.motion.settle).toBe("400ms");
  });

  it("generates design documentation", () => {
    const docs = generateDesignDocumentation();
    expect(docs.componentGuide.length).toBeGreaterThan(0);
    expect(docs.accessibilityGuide.standard).toBe("WCAG AA");
    expect(docs.themeDocumentation.themes).toContain("corporate");
  });
});

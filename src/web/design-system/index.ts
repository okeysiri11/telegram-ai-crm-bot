/** Enterprise Design System public API — Sprint 26.2 */
export { tokens, colors, fonts, fontSizes, fontWeights, radii, shadows, spacing, zIndex, breakpoints, motion, opacity } from "./tokens";
export { colorSystem } from "./colors";
export { typography } from "./typography";
export { spacingSystem } from "./spacing";
export { elevationSystem } from "./elevation";
export { gridSystem } from "./grid";
export { responsiveEngine } from "./responsive";
export { animationEngine } from "./animation";
export { accessibilityManager } from "./accessibility";
export { componentCatalog } from "./catalog";
export { themeEngine, applyTheme } from "./theme";
export type { ThemeId, BrandOverrides } from "./theme";
export { generateDesignDocumentation } from "./docs";
export { Icon, iconLibrary } from "./icons";
export type { IconName } from "./icons";

export const DESIGN_SYSTEM_VERSION = "9.0.6";
export const DESIGN_SYSTEM_PATH = "src/web/design-system";

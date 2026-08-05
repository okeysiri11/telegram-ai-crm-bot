/**
 * Enterprise City Graphics Engine — Theme Engine.
 * Sprint CG-2. City themes (`Light`, `Dark`, `Enterprise`, `Cyber`, future) are presentation skins
 * layered on the platform's real theme system (`design-system/theme`) — this module never redefines
 * `ThemeId` or introduces a second color palette. `Light`/`Dark` map straight onto the real themes.
 * `Enterprise` and `Cyber` are City-specific *brand accents* applied on top of the real `corporate`
 * and `dark` themes via `BrandOverrides`, the same mechanism any tenant brand override already uses —
 * no duplicated color definitions anywhere in this file.
 */

import { applyTheme, type BrandOverrides, type ThemeId } from "../../../design-system/theme";
import { colors } from "../../../design-system/tokens";
import type { CityGraphicsTheme } from "./types";

type CityThemeDefinition = {
  /** The real underlying platform theme this City theme rides on. */
  baseTheme: ThemeId;
  /** Optional accent layered via the real `BrandOverrides` mechanism — not a new color system. */
  brand?: BrandOverrides;
};

const CITY_THEMES: Record<CityGraphicsTheme, CityThemeDefinition> = {
  light: { baseTheme: "light" },
  dark: { baseTheme: "dark" },
  enterprise: { baseTheme: "corporate", brand: { primary: colors.secondary.DEFAULT, primarySoft: colors.secondary.soft } },
  cyber: { baseTheme: "dark", brand: { primary: colors.info.DEFAULT, primarySoft: colors.info.soft } },
};

/** Apply a City graphics theme — delegates to the real `applyTheme`, adding no rendering of its own. */
export function applyCityGraphicsTheme(theme: CityGraphicsTheme): void {
  const def = CITY_THEMES[theme];
  applyTheme(def.baseTheme, def.brand);
}

/** All City theme ids — future themes register here without touching `applyCityGraphicsTheme`'s logic. */
export function availableCityThemes(): CityGraphicsTheme[] {
  return Object.keys(CITY_THEMES) as CityGraphicsTheme[];
}

/** The real platform `ThemeId` a given City theme rides on — for callers that need the base value. */
export function baseThemeFor(theme: CityGraphicsTheme): ThemeId {
  return CITY_THEMES[theme].baseTheme;
}

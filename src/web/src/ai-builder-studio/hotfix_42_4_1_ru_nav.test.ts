/**
 * Hotfix 42.4.1 — Concierge Builder nav fully Russian via BUILDER_NAV_RU.
 */

import { describe, expect, it } from "vitest";
import { BUILDER_CATALOG } from "../../platform-builder/managers/builderRegistry";
import { BUILDER_NAV_RU, builderDisplayName, localizeLabel } from "@/i18n/platformGlossary";

const ALLOWED_ACRONYMS = /^(AI|CRM|ERP|API|MCP|JWT|OAuth|OKR|PDF)$/;

function hasForbiddenEnglish(label: string): boolean {
  // Latin letters that form English words (not only acronyms / Cyrillic / digits / punctuation)
  if (!/[A-Za-z]{3,}/.test(label)) return false;
  const tokens = label.split(/[\s·\-—,/&]+/).filter(Boolean);
  return tokens.some((t) => {
    if (!/^[A-Za-z]/.test(t)) return false;
    const bare = t.replace(/[^A-Za-z]/g, "");
    if (!bare) return false;
    if (ALLOWED_ACRONYMS.test(bare)) return false;
    // Product brand kept intentionally
    if (bare === "OTC" || bare === "Crypto") return false;
    return /[a-z]/.test(bare) || (bare.length > 3 && /^[A-Z][a-z]/.test(t));
  });
}

describe("Hotfix 42.4.1 Concierge Builder RU nav", () => {
  it("every BUILDER_CATALOG id has a Russian nav label", () => {
    for (const b of BUILDER_CATALOG) {
      expect(BUILDER_NAV_RU[b.id], `missing RU for ${b.id}`).toBeTruthy();
      const display = builderDisplayName(b.id, b.name);
      // Catalog names are already RU (42.5); display must match nav dictionary and stay RU-first.
      expect(display).toBe(BUILDER_NAV_RU[b.id]);
      expect(hasForbiddenEnglish(display), `${b.id} → ${display}`).toBe(false);
    }
  });

  it("localizes classic English builder titles from the user list", () => {
    const samples = [
      "Concierge Builder",
      "Dashboard",
      "Universal Builder Framework",
      "Vertical Builder",
      "AI Builder Studio",
      "AI Team Center",
      "Workflow Center",
      "Enterprise City",
      "Enterprise Data Fabric",
      "Enterprise Marketplace",
      "Builder Academy",
      "Visual Director Engine",
      "Visual Theme Engine",
      "Workflow Intelligence OS",
      "Enterprise Strategy Engine",
      "Enterprise Mission Control",
      "Predictive Intelligence",
      "Self-Learning Enterprise",
    ];
    for (const s of samples) {
      const ru = localizeLabel(s);
      expect(ru, s).not.toBe(s);
      expect(hasForbiddenEnglish(ru), `${s} → ${ru}`).toBe(false);
    }
  });
});

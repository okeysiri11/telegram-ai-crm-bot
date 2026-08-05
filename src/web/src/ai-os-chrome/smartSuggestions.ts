/**
 * Path-aware smart suggestions — Sprint 32.4 / EP-04 Advisor format.
 * Observation · Why · Action · Impact · Confidence — no new AI Engine.
 */

import type { LiveEnterpriseSnapshot } from "@/live-ops";
import {
  asAdvisorRecommendation,
  filterAdvisorSeen,
  type AdvisorRecommendation,
  type ConfidenceLevel,
} from "./aiPersonality";
import { getBuilding } from "@/enterprise-city/cityCatalog";
import { getCityFocus, advisorHintForBuilding } from "@/enterprise-city/cityVisualLanguage";
import { CITY_STATUS_SEED } from "@/enterprise-city/cityCatalog";

export type SmartSuggestion = {
  id: string;
  /** Compat headline (= action) */
  title: string;
  /** Compat short why */
  detail: string;
  route: string;
  tone: "action" | "attention" | "insight";
  observation: string;
  why: string;
  action: string;
  impact: string;
  confidence: ConfidenceLevel;
};

function sug(
  id: string,
  observation: string,
  why: string,
  action: string,
  impact: string,
  route: string,
  tone: SmartSuggestion["tone"],
  confidence: ConfidenceLevel = "medium",
): SmartSuggestion {
  return {
    id,
    title: action,
    detail: why,
    route,
    tone,
    observation,
    why,
    action,
    impact,
    confidence,
  };
}

const BY_SECTION: Record<string, SmartSuggestion[]> = {
  crm: [
    sug(
      "crm_create",
      "Pipeline needs a fresh lead capture.",
      "Empty intake slows revenue this week.",
      "Create a CRM client",
      "Faster qualification cycle",
      "/workspace/crm",
      "action",
      "high",
    ),
    sug(
      "crm_overdue",
      "Overdue deals remain open.",
      "Aging pipeline raises forecast risk.",
      "Review overdue deals",
      "Protect close rate",
      "/workspace/crm",
      "attention",
      "high",
    ),
    sug(
      "crm_ai",
      "Funnel needs an AI reading.",
      "Owner decisions improve with a short brief.",
      "Open AI funnel brief",
      "Clear next close priorities",
      "/platform-builder/ai-team",
      "insight",
      "medium",
    ),
  ],
  knowledge: [
    sug(
      "kb_new",
      "New Knowledge documents are available.",
      "Answers should use approved sources.",
      "Review Knowledge Base",
      "Fewer incorrect guidance loops",
      "/platform-builder/knowledge",
      "insight",
      "medium",
    ),
    sug(
      "kb_docs",
      "Workspace documents are ready.",
      "Operational files belong next to decisions.",
      "Open Documents",
      "Faster retrieval in context",
      "/workspace/docs",
      "action",
      "high",
    ),
  ],
  city: [
    sug(
      "city_prod",
      "Production contour is active on the map.",
      "Live buildings show where work concentrates.",
      "Inspect Production in City",
      "Shorter path to the right module",
      "/enterprise-city",
      "attention",
      "medium",
    ),
    sug(
      "city_mc",
      "Ops health should be confirmed.",
      "City navigation is safer with MC status.",
      "Check Mission Control",
      "Avoid acting on a degraded system",
      "/platform-builder/mission-control",
      "action",
      "high",
    ),
    sug(
      "city_tower",
      "Control Tower holds escalations from the map.",
      "Critical buildings need an owner decision path.",
      "Open Control Tower",
      "Clear escalations from City glance",
      "/platform-builder/control-tower",
      "attention",
      "high",
    ),
    sug(
      "city_dash",
      "Dashboard is the ownership companion to City.",
      "Map glance + Morning Brief = full executive picture.",
      "Open Dashboard",
      "10-second ownership context",
      "/dashboard",
      "insight",
      "high",
    ),
  ],
  analytics: [
    sug(
      "an_kpi",
      "A KPI signal changed.",
      "Owner attention belongs on measurable moves.",
      "Open Intelligence",
      "Faster response to trend shifts",
      "/platform-builder/intelligence",
      "attention",
      "medium",
    ),
    sug(
      "an_dash",
      "Executive Mode summarizes ownership priorities.",
      "Dense analytics should collapse to decisions.",
      "Open Executive Mode",
      "10-second morning clarity",
      "/dashboard?mode=executive",
      "insight",
      "high",
    ),
  ],
  dashboard: [
    sug(
      "dash_attn",
      "Attention items are waiting on the Brief.",
      "Unresolved signals compound through the day.",
      "Work Attention in Control Tower",
      "Clear decisions before noon",
      "/platform-builder/control-tower",
      "attention",
      "high",
    ),
    sug(
      "dash_live",
      "Operational pulse needs a glance.",
      "Health informs every other recommendation.",
      "Open Mission Control health",
      "Stable base for owner actions",
      "/platform-builder/mission-control",
      "action",
      "high",
    ),
    sug(
      "dash_conc",
      "Morning Brief can go deeper with Concierge.",
      "Advisor context improves follow-through.",
      "Ask Concierge for detail",
      "One guided path instead of browsing",
      "/platform-builder/concierge",
      "insight",
      "medium",
    ),
  ],
  ai: [
    sug(
      "ai_team",
      "Agents may be running without owner review.",
      "Unwatched automation creates silent risk.",
      "Review AI Team agents",
      "Controlled automation spend",
      "/platform-builder/ai-team",
      "action",
      "high",
    ),
    sug(
      "ai_conc",
      "Concierge profile shapes daily advice.",
      "Tone and access must match the owner.",
      "Configure Concierge",
      "Advice stays on-brand and relevant",
      "/platform-builder/concierge",
      "insight",
      "medium",
    ),
  ],
  finance: [
    sug(
      "fin_close",
      "Period close hygiene is pending.",
      "Late close blocks trustworthy forecasts.",
      "Check period close",
      "Reliable finance decisions",
      "/workspace/finance",
      "attention",
      "high",
    ),
  ],
  marketplace: [
    sug(
      "mkt_packs",
      "Enterprise packs are available.",
      "Packs shorten time-to-value without rebuilds.",
      "Browse Marketplace packs",
      "Faster capability coverage",
      "/platform-builder/solution-hub",
      "insight",
      "medium",
    ),
  ],
  builder: [
    sug(
      "bld_studio",
      "Builder Studio is ready for a specialist.",
      "A focused agent reduces repetitive owner work.",
      "Open Builder Studio",
      "Reusable automation in days, not weeks",
      "/platform-builder/builder-studio",
      "action",
      "medium",
    ),
  ],
  default: [
    sug(
      "def_crm",
      "Customer work is the usual first lever.",
      "Revenue hygiene beats browsing modules.",
      "Open CRM",
      "Immediate pipeline visibility",
      "/workspace/crm",
      "action",
      "medium",
    ),
    sug(
      "def_ai",
      "Executive Advisor is available.",
      "Ask for a decision, not a chat thread.",
      "Open AI Concierge",
      "Guided next action in seconds",
      "/platform-builder/concierge",
      "insight",
      "high",
    ),
    sug(
      "def_mc",
      "Platform health should be known first.",
      "Advice is weaker on an unhealthy base.",
      "Open Mission Control",
      "Safe operating baseline",
      "/platform-builder/mission-control",
      "attention",
      "high",
    ),
    sug(
      "def_dash",
      "Command Center holds the ownership view.",
      "Return when priorities feel scattered.",
      "Back to Dashboard",
      "Restore executive focus",
      "/dashboard",
      "action",
      "high",
    ),
  ],
};

const KB_HINT = sug(
  "kb_aware",
  "Knowledge awareness detected in live signals.",
  "Advice should cite approved documents when available.",
  "Review Knowledge updates",
  "Higher answer trust",
  "/platform-builder/knowledge",
  "insight",
  "medium",
);

export function sectionKeyFromPath(pathname: string): string {
  if (pathname.includes("/crm") || pathname.includes("sales")) return "crm";
  if (pathname.includes("/knowledge") || pathname.includes("/docs")) return "knowledge";
  if (pathname.includes("enterprise-city") || pathname.includes("digital-twin") || pathname.includes("enterprise-twin"))
    return "city";
  if (pathname.includes("intelligence") || pathname.includes("analytics")) return "analytics";
  if (pathname.includes("/dashboard")) return "dashboard";
  if (pathname.includes("ai-team") || pathname.includes("/concierge") || pathname.includes("/workspace/ai")) return "ai";
  if (pathname.includes("finance")) return "finance";
  if (pathname.includes("marketplace") || pathname.includes("solution-hub")) return "marketplace";
  if (pathname.includes("builder-studio") || pathname.includes("ai-builder")) return "builder";
  return "default";
}

function knowledgeAwareFromSnapshot(snapshot?: LiveEnterpriseSnapshot | null): boolean {
  if (!snapshot) return false;
  const kb = snapshot.health.some((h) => (h.id === "knowledge" || h.id === "documents") && h.ok);
  const hint = snapshot.activeModules.some((m) => /knowledge|doc/i.test(m));
  const act = snapshot.activity.some((a) =>
    /knowledge|документ|docs/i.test(`${a.title} ${a.detail} ${a.moduleHint || ""}`),
  );
  const rec = snapshot.recommendations.some((r) => /knowledge|document|docs/i.test(r.title));
  return Boolean(hint || act || rec || kb);
}

export function toAdvisor(s: SmartSuggestion): AdvisorRecommendation {
  return asAdvisorRecommendation(s);
}

export function suggestionsForPath(
  pathname: string,
  limit = 5,
  snapshot?: LiveEnterpriseSnapshot | null,
): SmartSuggestion[] {
  const key = sectionKeyFromPath(pathname);
  const primary = [...(BY_SECTION[key] || BY_SECTION.default)];
  if (knowledgeAwareFromSnapshot(snapshot) && key !== "knowledge") {
    primary.unshift(KB_HINT);
  }
  // EP-05: Concierge understands selected City building
  if (key === "city" || pathname.includes("enterprise-city") || pathname.includes("concierge")) {
    const focus = getCityFocus();
    if (focus) {
      const b = getBuilding(focus);
      const seed = CITY_STATUS_SEED[focus];
      if (b && seed) {
        const hint = advisorHintForBuilding(focus, seed);
        primary.unshift(
          sug(
            `city_focus_${focus}`,
            hint.observation,
            hint.why,
            hint.action,
            hint.impact,
            hint.route,
            seed.tone === "alert" ? "attention" : "action",
            seed.tone === "alert" ? "high" : "medium",
          ),
        );
      }
    }
  }
  // Snapshot-aware reorder: health issues first
  if (snapshot?.health.some((h) => !h.ok)) {
    primary.sort((a, b) => (a.tone === "attention" ? -1 : 0) - (b.tone === "attention" ? -1 : 0));
  }
  const seen = new Set<string>();
  const padded: SmartSuggestion[] = [];
  for (const s of [...primary, ...BY_SECTION.default]) {
    if (padded.length >= limit + 2) break;
    if (seen.has(s.id)) continue;
    padded.push(s);
    seen.add(s.id);
  }
  const filtered = filterAdvisorSeen(padded, 2);
  return filtered.slice(0, Math.max(2, Math.min(limit, filtered.length)));
}

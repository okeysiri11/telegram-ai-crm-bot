/**
 * AI Personality & Intelligent Interaction — EP-04.
 * Executive Advisor voice over existing Concierge / Brief / suggestions.
 * No AI Core / Engine / Runtime / Store changes.
 */

export const AI_PERSONALITY_VERSION = "1.0";

export const ENTERPRISE_AI_TONE = {
  calm: true,
  confident: true,
  businesslike: true,
  concise: true,
  proactive: true,
  respectful: true,
  /** Forbidden: chatbot cheer, emoji spam, hype */
  noFluff: true,
} as const;

/** Language policy — EP-04 §7 */
export type AiSurfaceLocale = "en_status" | "ru_city" | "org_workspace" | "advisor";

export const LANGUAGE_POLICY = {
  dashboardOwner: "en_status" as const,
  enterpriseCity: "ru_city" as const,
  workspace: "org_workspace" as const,
  concierge: "advisor" as const,
  note: {
    en_status: "Dashboard status badges and health labels stay English.",
    ru_city: "Enterprise City navigation copy uses RU/UA localization.",
    org_workspace: "Workspace module copy follows organization language.",
    advisor: "Executive Advisor voice: calm RU/EN mix; status chips English.",
  },
} as const;

export type ConfidenceLevel = "high" | "medium" | "low";

export type AdvisorRecommendation = {
  id: string;
  /** Observation — what is true now */
  observation: string;
  /** Why it matters */
  why: string;
  /** Suggested action */
  action: string;
  /** Expected impact */
  impact: string;
  route: string;
  confidence: ConfidenceLevel;
  tone: "action" | "attention" | "insight";
};

const SESSION_KEY = "ewp_ai_advisor_seen_v1";

function readSeen(): Set<string> {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return new Set();
    const arr = JSON.parse(raw) as string[];
    return new Set(Array.isArray(arr) ? arr : []);
  } catch {
    return new Set();
  }
}

function writeSeen(ids: Set<string>) {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify([...ids].slice(-40)));
  } catch {
    /* ignore */
  }
}

/** Session memory — avoid repeating the same advice in one browser session. */
export function markAdvisorSeen(id: string) {
  const seen = readSeen();
  seen.add(id);
  writeSeen(seen);
}

export function filterAdvisorSeen<T extends { id: string }>(items: T[], minKeep = 2): T[] {
  const seen = readSeen();
  const fresh = items.filter((i) => !seen.has(i.id));
  if (fresh.length >= minKeep) return fresh;
  return items;
}

export function confidenceLabel(level: ConfidenceLevel, locale: AiSurfaceLocale = "advisor"): string {
  if (locale === "en_status" || locale === "advisor") {
    if (level === "high") return "High confidence";
    if (level === "medium") return "Likely";
    return "Exploratory";
  }
  if (level === "high") return "Висока впевненість";
  if (level === "medium") return "Ймовірно";
  return "Орієнтовно";
}

export function confidenceBadgeTone(level: ConfidenceLevel): "success" | "default" | "warning" {
  if (level === "high") return "success";
  if (level === "medium") return "default";
  return "warning";
}

/** Quiet confidence for UI density (one short word). */
export function confidenceShort(level: ConfidenceLevel): string {
  if (level === "high") return "High";
  if (level === "medium") return "Likely";
  return "Explore";
}

export function toneChip(tone: AdvisorRecommendation["tone"]): string {
  if (tone === "attention") return "Attention";
  if (tone === "insight") return "Insight";
  return "Action";
}

/** Contextual one-liner for Concierge dock — tied to section + live state. */
export function advisorContextLine(opts: {
  section: string;
  company: string;
  healthOk: number;
  healthTotal: number;
  unread: number;
  aiBusy: boolean;
}): string {
  const { section, company, healthOk, healthTotal, unread, aiBusy } = opts;
  const health = `${healthOk}/${healthTotal}`;
  if (aiBusy) {
    return `${company}: AI is working — I will refine advice when results settle.`;
  }
  if (unread > 0 && (section === "dashboard" || section === "default")) {
    return `${company}: ${unread} signals need a decision. Start with Attention.`;
  }
  if (healthOk < healthTotal) {
    return `${company}: health ${health}. Review Mission Control before new work.`;
  }
  switch (section) {
    case "crm":
      return `${company}: CRM context active — focus on pipeline risk and next close.`;
    case "knowledge":
      return `${company}: Knowledge context — prefer approved documents over guesses.`;
    case "city":
      return `${company}: City map open — use buildings as navigation, not decoration.`;
    case "analytics":
      return `${company}: Intelligence view — prioritize KPI moves with owner impact.`;
    case "dashboard":
      return `${company}: Morning priorities first — then deepen in Control Tower.`;
    case "ai":
      return `${company}: AI Team context — confirm running agents before new tasks.`;
    case "finance":
      return `${company}: Finance context — close period hygiene before expansion.`;
    default:
      return `${company}: Ready. Ask for the next decision, not a chat.`;
  }
}

export function advisorGreeting(hour = new Date().getHours()): string {
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

/** Map legacy recommendation tone → confidence. */
export function confidenceFromRecTone(tone: string): ConfidenceLevel {
  if (tone === "risk" || tone === "today") return "high";
  if (tone === "improve") return "medium";
  return "medium";
}

export function formatAdvisorBlocks(rec: AdvisorRecommendation): {
  observation: string;
  why: string;
  action: string;
  impact: string;
} {
  return {
    observation: rec.observation,
    why: rec.why,
    action: rec.action,
    impact: rec.impact,
  };
}

/** Build advisor recommendation from path suggestion fields. */
export function asAdvisorRecommendation(input: {
  id: string;
  observation: string;
  why: string;
  action: string;
  impact: string;
  route: string;
  confidence?: ConfidenceLevel;
  tone: AdvisorRecommendation["tone"];
}): AdvisorRecommendation {
  return {
    id: input.id,
    observation: input.observation,
    why: input.why,
    action: input.action,
    impact: input.impact,
    route: input.route,
    confidence: input.confidence || "medium",
    tone: input.tone,
  };
}

export const ADVISOR_VOICE_SAMPLES = {
  morning: "Here is what matters for ownership today — not a chat backlog.",
  decision: "Observation, why it matters, the action, and the expected impact.",
  calm: "No critical signals. Use the window for opportunities.",
  risk: "Treat this as a decision item before new initiatives.",
} as const;

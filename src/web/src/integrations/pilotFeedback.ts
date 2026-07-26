/**
 * Central Pilot Feedback — Sprint 30.7.
 * Submits via existing EPR (/api/enterprise-epr/v1/feedback) → EOC → EPI.
 * Classifies via ELE; Critical issues open OBS incidents. No parallel feedback stack.
 */

import { apiFetch } from "@/integrations/apiClient";
import { hubIntegrations } from "@/integrations/hub";
import { getIdentityContext } from "@/integrations/apiClient";
import { telemetry } from "@/integrations/telemetry";

export type FeedbackKind = "review" | "idea" | "error" | "rating";

export type FeedbackCategory =
  | "user_feedback"
  | "ai_feedback"
  | "error"
  | "warning"
  | "suggestion"
  | "ux_issue"
  | "missing_feature";

export type TriageSeverity = "Critical" | "High" | "Medium" | "Low";

export type PilotFeedbackRecord = {
  feedback_id?: string;
  kind: FeedbackKind;
  category: FeedbackCategory;
  message: string;
  feature: string;
  module: string;
  severity: TriageSeverity;
  classification?: Record<string, unknown>;
  incident_id?: string;
  trace_id: string;
  user_id?: string;
  created_at: string;
};

const EPR = "/api/enterprise-epr/v1";
const ELE = "/api/enterprise-ele/v1";
const OBS = hubIntegrations.monitoring;

const MODULE_KEYWORDS: Record<string, string[]> = {
  automotive: ["auto", "lead", "crm", "dealer", "vehicle", "automotive"],
  beauty: ["beauty", "salon", "appointment", "stylist", "bos", "bws", "bcj", "haircut"],
  cafe: ["cafe", "restaurant", "kitchen", "menu", "reservation", "table", "order", "waiter"],
  agriculture: [
    "agro",
    "agriculture",
    "farm",
    "harvest",
    "grain",
    "warehouse",
    "shipment",
    "commodity",
    "export",
    "container",
  ],
  legal: [
    "legal",
    "law",
    "case",
    "hearing",
    "court",
    "contract",
    "document",
    "signature",
    "counsel",
    "litigation",
  ],
  crypto: [
    "bidex",
    "crypto",
    "wallet",
    "otc",
    "p2p",
    "kyc",
    "aml",
    "treasury",
    "settlement",
    "bitcoin",
  ],
  identity: ["login", "jwt", "auth", "permission", "session", "token"],
  mission_control: ["mission", "executive", "cockpit"],
  concierge: ["concierge", "ai agent", "assistant"],
  notifications: ["notification", "email", "alert", "comms"],
  observability: ["telemetry", "metric", "log", "obs"],
  analytics: ["analytics", "dashboard", "pipeline", "bi"],
  web_shell: ["ui", "ux", "layout", "navigation", "button", "form"],
};

function categoryToKind(category: FeedbackCategory): FeedbackKind {
  switch (category) {
    case "error":
      return "error";
    case "suggestion":
    case "missing_feature":
      return "idea";
    case "ai_feedback":
    case "warning":
    case "ux_issue":
    case "user_feedback":
    default:
      return "review";
  }
}

export function assignModule(message: string, feature = ""): string {
  const text = `${message} ${feature}`.toLowerCase();
  for (const [mod, keys] of Object.entries(MODULE_KEYWORDS)) {
    if (keys.some((k) => text.includes(k))) return mod;
  }
  return "automotive";
}

export function classifySeverity(
  category: FeedbackCategory,
  eleClass?: string,
  message = "",
): TriageSeverity {
  const lower = `${message} ${eleClass || ""}`.toLowerCase();
  if (
    category === "error" ||
    /critical|outage|down|security|data loss|cannot login/.test(lower)
  ) {
    return /critical|outage|data loss|security/.test(lower) ? "Critical" : "High";
  }
  if (category === "warning" || eleClass === "complaint" || eleClass === "ux_issue") {
    return "Medium";
  }
  if (category === "missing_feature" || eleClass === "new_feature") return "Medium";
  return "Low";
}

function traceId(): string {
  return `pfb_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

export async function classifyFeedbackText(text: string): Promise<Record<string, unknown>> {
  const res = await apiFetch(`${ELE}/feedback`, {
    method: "POST",
    body: JSON.stringify({ text }),
  });
  const body = (await res.json()) as Record<string, unknown>;
  if (!res.ok) return { class: "suggestion", auto_classified: false, error: body.error };
  return body;
}

export async function submitPilotFeedback(input: {
  category: FeedbackCategory;
  message: string;
  feature?: string;
  rating?: number;
  moduleHint?: string;
}): Promise<PilotFeedbackRecord> {
  const ctx = getIdentityContext();
  const tid = traceId();
  const classification = await classifyFeedbackText(input.message);
  const eleClass = String(classification.class || "");
  const module = input.moduleHint || assignModule(input.message, input.feature || "");
  const severity = classifySeverity(input.category, eleClass, input.message);
  const kind = categoryToKind(input.category);
  const feature = input.feature || module;

  const res = await apiFetch(`${EPR}/feedback`, {
    method: "POST",
    body: JSON.stringify({
      kind,
      message: `[${input.category}] [${severity}] [${module}] trace=${tid} ${input.message}`,
      rating: input.rating,
      feature,
      user_id: ctx.userId || ctx.email || "",
    }),
  });
  const body = (await res.json()) as Record<string, unknown>;
  if (!res.ok) throw new Error(String(body.error || "Feedback submit failed"));

  let incidentId: string | undefined;
  if (severity === "Critical" || severity === "High") {
    const inc = await apiFetch(`${OBS}/incidents`, {
      method: "POST",
      body: JSON.stringify({
        action: "open",
        service: module,
        severity: severity === "Critical" ? "critical" : "error",
        owner: "pilot_ops",
        root_cause: `pilot_feedback:${tid}`,
        sla_minutes: severity === "Critical" ? 30 : 120,
      }),
    });
    if (inc.ok) {
      const incBody = (await inc.json()) as Record<string, unknown>;
      incidentId = String(incBody.incident_id || "");
    }
  }

  await telemetry.audit(
    "pilot_feedback",
    `${tid};${severity};${module};${kind}`,
  );
  await telemetry.businessEvent(`pilot_feedback_${severity.toLowerCase()}`);

  const record: PilotFeedbackRecord = {
    feedback_id: String(body.feedback_id || body.id || ""),
    kind,
    category: input.category,
    message: input.message,
    feature,
    module,
    severity,
    classification,
    incident_id: incidentId,
    trace_id: tid,
    user_id: ctx.userId || ctx.email || undefined,
    created_at: new Date().toISOString(),
  };

  const key = "ewp_pilot_feedback_v1";
  try {
    const prev = JSON.parse(localStorage.getItem(key) || "[]") as PilotFeedbackRecord[];
    localStorage.setItem(key, JSON.stringify([record, ...prev].slice(0, 50)));
  } catch {
    /* ignore */
  }
  return record;
}

export function listLocalFeedback(): PilotFeedbackRecord[] {
  try {
    return JSON.parse(localStorage.getItem("ewp_pilot_feedback_v1") || "[]") as PilotFeedbackRecord[];
  } catch {
    return [];
  }
}

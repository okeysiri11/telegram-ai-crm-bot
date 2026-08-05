/**
 * CEO Morning Brief derive — EP-01 Executive Experience.
 * Pure composition over LiveEnterpriseSnapshot + existing recommendation signals.
 * No new Engine / Store / Runtime.
 */

import type { LiveEnterpriseSnapshot, RecommendationItem } from "@/live-ops";
import { suggestionsForPath, type SmartSuggestion } from "@/ai-os-chrome/smartSuggestions";
import { advisorGreeting, confidenceFromRecTone, ADVISOR_VOICE_SAMPLES } from "@/ai-os-chrome/aiPersonality";

export type BriefItem = {
  id: string;
  title: string;
  /** Observation — what is true now */
  what: string;
  /** Why it matters */
  why: string;
  /** Suggested action */
  next: string;
  /** Expected impact */
  impact: string;
  route: string;
  tone: "ok" | "watch" | "alert" | "opportunity";
  confidence?: "high" | "medium" | "low";
};

export type MorningBrief = {
  greeting: string;
  company: string;
  tone: "calm" | "watch" | "alert";
  summaryLine: string;
  happening: BriefItem[];
  attention: BriefItem[];
  aiActions: BriefItem[];
  risks: BriefItem[];
  opportunities: BriefItem[];
  healthOk: number;
  healthTotal: number;
  unread: number;
};

function greetingForHour(d = new Date()): string {
  // Dashboard owner status language prefers English greetings (EP-04 policy).
  return advisorGreeting(d.getHours());
}

function recToAction(r: RecommendationItem, i: number): BriefItem {
  const route =
    /crm|сделк|клиент/i.test(r.title)
      ? "/workspace/crm"
      : /mission|control|health/i.test(r.title)
        ? "/platform-builder/mission-control"
        : /team|agent|ai/i.test(r.title)
          ? "/platform-builder/ai-team"
          : "/platform-builder/concierge";
  const why =
    r.tone === "risk"
      ? "This risk can affect operations today."
      : r.tone === "today"
        ? "There is a decision window before end of day."
        : r.tone === "improve"
          ? "A small improvement will produce a measurable effect."
          : "This action carries clear owner value.";
  const impact =
    r.tone === "risk"
      ? "Lower operational exposure"
      : r.tone === "today"
        ? "Decision cleared today"
        : "Incremental performance gain";
  return {
    id: r.id || `rec_${i}`,
    title: r.title,
    what: r.title,
    why,
    next: "Open and confirm",
    impact,
    route,
    tone: r.tone === "risk" ? "alert" : "opportunity",
    confidence: confidenceFromRecTone(r.tone),
  };
}

function suggestToAction(s: SmartSuggestion): BriefItem {
  return {
    id: s.id,
    title: s.action,
    what: s.observation,
    why: s.why,
    next: s.action,
    impact: s.impact,
    route: s.route,
    tone: s.tone === "attention" ? "watch" : "opportunity",
    confidence: s.confidence,
  };
}

export function deriveMorningBrief(
  snapshot: LiveEnterpriseSnapshot,
  opts: {
    company?: string;
    unread?: number;
    conciergeName?: string;
  } = {},
): MorningBrief {
  const company = opts.company || "Enterprise";
  const unread = opts.unread ?? 0;
  const healthOk = snapshot.health.filter((h) => h.ok).length;
  const healthTotal = snapshot.health.length || 1;
  const healthBad = snapshot.health.filter((h) => !h.ok);
  const aiErrors = snapshot.aiOps.errors || [];
  const running = snapshot.aiOps.running || [];

  const happening: BriefItem[] = snapshot.activity.slice(0, 4).map((a, i) => ({
    id: a.id || `act_${i}`,
    title: a.title,
    what: a.title,
    why: a.detail || `Source: ${a.source}`,
    next: a.moduleHint ? `Open ${a.moduleHint}` : "Review Mission Control",
    impact: "Situational awareness for ownership",
    route:
      a.kind === "ai"
        ? "/platform-builder/ai-team"
        : a.source === "mission_control"
          ? "/platform-builder/mission-control"
          : "/platform-builder/control-tower",
    tone: a.kind === "notification" ? "watch" : "ok",
    confidence: "medium",
  }));

  if (!happening.length) {
    happening.push({
      id: "calm",
      title: "System calm",
      what: "No critical events",
      why: ADVISOR_VOICE_SAMPLES.calm,
      next: "Open Mission Control",
      impact: "Safe window for opportunity work",
      route: "/platform-builder/mission-control",
      tone: "ok",
      confidence: "high",
    });
  }

  const attention: BriefItem[] = [];
  if (unread > 0) {
    attention.push({
      id: "attn_notif",
      title: `${unread} notifications`,
      what: `Unread signals: ${unread}`,
      why: "Some may require an owner decision.",
      next: "Open Control Tower",
      impact: "Fewer missed escalations",
      route: "/platform-builder/control-tower",
      tone: "watch",
      confidence: "high",
    });
  }
  for (const h of healthBad.slice(0, 3)) {
    attention.push({
      id: `attn_h_${h.id}`,
      title: h.label,
      what: `${h.label}: ${h.detail || "degraded"}`,
      why: "System health affects trust in every operation.",
      next: "Check Mission Control",
      impact: "Restore operating baseline",
      route: "/platform-builder/mission-control",
      tone: "alert",
      confidence: "high",
    });
  }
  for (const e of aiErrors.slice(0, 2)) {
    attention.push({
      id: `attn_ai_${e}`,
      title: "AI fault",
      what: e,
      why: "AI faults can stop automation mid-flight.",
      next: "Open AI Runtime",
      impact: "Recover automation reliability",
      route: "/platform-builder/runtime",
      tone: "alert",
      confidence: "high",
    });
  }
  if (!attention.length) {
    attention.push({
      id: "attn_none",
      title: "No attention required",
      what: "No critical signals",
      why: "Focus can shift to growth opportunities.",
      next: "Review KPI",
      impact: "Owner time on upside",
      route: "/dashboard?mode=executive",
      tone: "ok",
      confidence: "high",
    });
  }

  const dashSuggestions = suggestionsForPath("/dashboard", 3, snapshot);
  const fromRecs = (snapshot.recommendations || []).slice(0, 3).map(recToAction);
  const aiActions: BriefItem[] = [
    ...fromRecs,
    ...dashSuggestions.filter((s) => !fromRecs.some((r) => r.what === s.observation || r.title === s.action)).map(suggestToAction),
  ].slice(0, 3);

  if (!aiActions.length) {
    aiActions.push({
      id: "ai_default",
      title: "Ask Executive Advisor",
      what: "Advisor is ready for the morning brief",
      why: ADVISOR_VOICE_SAMPLES.morning,
      next: "Open Concierge",
      impact: "One guided path for the day",
      route: "/platform-builder/concierge",
      tone: "opportunity",
      confidence: "high",
    });
  }

  const risks: BriefItem[] = [
    ...healthBad.slice(0, 2).map((h) => ({
      id: `risk_${h.id}`,
      title: h.label,
      what: h.detail || "Health signal",
      why: ADVISOR_VOICE_SAMPLES.risk,
      next: "Resolve in Control Tower",
      impact: "Lower service and data risk",
      route: "/platform-builder/control-tower",
      tone: "alert" as const,
      confidence: "high" as const,
    })),
    ...aiErrors.slice(0, 1).map((e) => ({
      id: `risk_ai_${e}`,
      title: "AI risk",
      what: e,
      why: "Automation may fail to complete.",
      next: "AI Runtime",
      impact: "Protect automated outcomes",
      route: "/platform-builder/runtime",
      tone: "alert" as const,
      confidence: "high" as const,
    })),
  ];
  if (!risks.length) {
    risks.push({
      id: "risk_none",
      title: "Risks under control",
      what: `${healthOk}/${healthTotal} health · AI ${running.length ? "active" : "idle"}`,
      why: "No active red zones.",
      next: "Digital Twin",
      impact: "Confidence to pursue opportunities",
      route: "/platform-builder/digital-twin",
      tone: "ok",
      confidence: "high",
    });
  }

  const opportunities: BriefItem[] = (
    [
      {
        id: "opp_mkt",
        title: "Marketplace packs",
        what: "Enterprise packs are available",
        why: "Capability growth without a rebuild.",
        next: "Open Marketplace",
        impact: "Faster time-to-value",
        route: "/platform-builder/solution-hub",
        tone: "opportunity",
        confidence: "medium",
      },
      {
        id: "opp_city",
        title: "Enterprise City",
        what: "Module map is ready",
        why: "Spatial navigation shortens path to the right contour.",
        next: "Open City",
        impact: "Faster module discovery",
        route: "/enterprise-city",
        tone: "opportunity",
        confidence: "medium",
      },
      running.length
        ? {
            id: "opp_ai",
            title: "AI already working",
            what: `${running.slice(0, 2).join(" · ")}`,
            why: "Results can be amplified via AI Team.",
            next: "AI Team",
            impact: "Higher yield from running agents",
            route: "/platform-builder/ai-team",
            tone: "opportunity",
            confidence: "medium",
          }
        : {
            id: "opp_builder",
            title: "Build a specialist",
            what: "Builder Studio is ready",
            why: "A focused agent reduces repetitive owner work.",
            next: "Builder Studio",
            impact: "Reusable automation",
            route: "/platform-builder/builder-studio",
            tone: "opportunity",
            confidence: "medium",
          },
    ] as BriefItem[]
  ).slice(0, 3);

  const tone: MorningBrief["tone"] =
    healthBad.length || aiErrors.length ? "alert" : unread > 0 || attention.some((a) => a.tone === "watch") ? "watch" : "calm";

  const summaryLine =
    tone === "alert"
      ? "Signals need attention — start with Attention, then confirm in Control Tower."
      : tone === "watch"
        ? "Day is stable, with a few items worth a decision review."
        : "Company under control. Advisor is ready to walk opportunities.";

  return {
    greeting: greetingForHour(),
    company,
    tone,
    summaryLine,
    happening,
    attention,
    aiActions,
    risks,
    opportunities,
    healthOk,
    healthTotal,
    unread,
  };
}

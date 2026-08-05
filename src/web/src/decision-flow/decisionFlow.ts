/**
 * Enterprise Intelligence & Decision Flow — EP-06.
 * Interaction logic only: Observation → … → Result.
 * No Engine / Store / Runtime / AI Core.
 */

export const DECISION_FLOW_VERSION = "1.0";

export type DecisionStep = "observe" | "understand" | "recommend" | "decide" | "act" | "result";

export const DECISION_CHAIN: { step: DecisionStep; label: string; question: string }[] = [
  { step: "observe", label: "Observation", question: "What is true now?" },
  { step: "understand", label: "Understanding", question: "Why does it matter?" },
  { step: "recommend", label: "Recommendation", question: "What should we do?" },
  { step: "decide", label: "Decision", question: "What do we choose?" },
  { step: "act", label: "Action", question: "Where do we act?" },
  { step: "result", label: "Result", question: "Did it work?" },
];

export type DecisionContext = {
  from: string;
  step: DecisionStep;
  focus?: string;
  label: string;
  nextRoute: string;
  nextCta: string;
  updatedAt: number;
};

const CTX_KEY = "ewp_decision_ctx_v1";

/** Cross-module decision companions — one system, not isolated apps. */
export const CROSS_MODULE_FLOW: Record<
  string,
  { next: string; cta: string; step: DecisionStep; why: string }
> = {
  "/dashboard": {
    next: "/platform-builder/control-tower",
    cta: "Decide in Control Tower",
    step: "decide",
    why: "Morning signals become owner decisions",
  },
  "/platform-builder/control-tower": {
    next: "/platform-builder/mission-control",
    cta: "Confirm live health",
    step: "act",
    why: "Validate the system before committing",
  },
  "/platform-builder/mission-control": {
    next: "/platform-builder/concierge",
    cta: "Ask Advisor to prioritize",
    step: "recommend",
    why: "Ops pulse → ranked next actions",
  },
  "/platform-builder/concierge": {
    next: "/platform-builder/builder-studio",
    cta: "Build the specialist",
    step: "act",
    why: "Advice becomes reusable automation",
  },
  "/platform-builder/builder-studio": {
    next: "/platform-builder/solution-hub",
    cta: "Find a pack in Marketplace",
    step: "act",
    why: "Prefer proven packs before custom build",
  },
  "/platform-builder/solution-hub": {
    next: "/workspace/crm",
    cta: "Apply in CRM",
    step: "result",
    why: "Capability must land in customer work",
  },
  "/workspace/crm": {
    next: "/platform-builder/knowledge",
    cta: "Capture learning in Knowledge",
    step: "result",
    why: "Close the loop with approved knowledge",
  },
  "/platform-builder/knowledge": {
    next: "/platform-builder/ai-team",
    cta: "Brief AI Team",
    step: "recommend",
    why: "Knowledge feeds better agent work",
  },
  "/platform-builder/ai-team": {
    next: "/dashboard?mode=executive",
    cta: "Return to Morning Brief",
    step: "observe",
    why: "Owner sees the outcome",
  },
  "/enterprise-city": {
    next: "/platform-builder/digital-twin",
    cta: "Open Digital Twin",
    step: "understand",
    why: "Map glance → structural twin",
  },
  "/platform-builder/digital-twin": {
    next: "/dashboard?mode=executive",
    cta: "Back to Dashboard",
    step: "decide",
    why: "Twin insight becomes an owner decision",
  },
};

export function pushDecisionContext(partial: Omit<DecisionContext, "updatedAt"> & { updatedAt?: number }) {
  const ctx: DecisionContext = { ...partial, updatedAt: partial.updatedAt || Date.now() };
  try {
    sessionStorage.setItem(CTX_KEY, JSON.stringify(ctx));
  } catch {
    /* ignore */
  }
  return ctx;
}

export function readDecisionContext(): DecisionContext | null {
  try {
    const raw = sessionStorage.getItem(CTX_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as DecisionContext;
    if (!parsed?.nextRoute || !parsed?.label) return null;
    // stale after 2h
    if (Date.now() - (parsed.updatedAt || 0) > 2 * 60 * 60 * 1000) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function clearDecisionContext() {
  try {
    sessionStorage.removeItem(CTX_KEY);
  } catch {
    /* ignore */
  }
}

/** Append decision context to a route without breaking existing query. */
export function withDecisionQuery(
  route: string,
  opts: { from: string; step: DecisionStep; focus?: string },
): string {
  const [path, qs] = route.split("?");
  const params = new URLSearchParams(qs || "");
  params.set("from", opts.from);
  params.set("step", opts.step);
  if (opts.focus) params.set("focus", opts.focus);
  const q = params.toString();
  return q ? `${path}?${q}` : path;
}

export function pathKey(pathname: string): string {
  if (pathname.startsWith("/dashboard")) return "/dashboard";
  if (pathname.includes("control-tower")) return "/platform-builder/control-tower";
  if (pathname.includes("mission-control")) return "/platform-builder/mission-control";
  if (pathname.includes("concierge")) return "/platform-builder/concierge";
  if (pathname.includes("builder-studio") || pathname.includes("ai-builder")) return "/platform-builder/builder-studio";
  if (pathname.includes("solution-hub") || pathname.includes("marketplace")) return "/platform-builder/solution-hub";
  if (pathname.includes("/crm")) return "/workspace/crm";
  if (pathname.includes("knowledge")) return "/platform-builder/knowledge";
  if (pathname.includes("ai-team")) return "/platform-builder/ai-team";
  if (pathname.includes("enterprise-city")) return "/enterprise-city";
  if (pathname.includes("digital-twin") || pathname.includes("enterprise-twin")) return "/platform-builder/digital-twin";
  return pathname;
}

export type ContinueDecision = {
  why: string;
  route: string;
  cta: string;
  step: DecisionStep;
  chainIndex: number;
};

export function resolveContinue(pathname: string, ctx?: DecisionContext | null): ContinueDecision | null {
  if (ctx?.nextRoute) {
    const idx = DECISION_CHAIN.findIndex((c) => c.step === ctx.step);
    return {
      why: ctx.label,
      route: withDecisionQuery(ctx.nextRoute, { from: pathKey(pathname), step: ctx.step, focus: ctx.focus }),
      cta: ctx.nextCta,
      step: ctx.step,
      chainIndex: Math.max(0, idx),
    };
  }
  const key = pathKey(pathname);
  const flow = CROSS_MODULE_FLOW[key];
  if (!flow) return null;
  const idx = DECISION_CHAIN.findIndex((c) => c.step === flow.step);
  return {
    why: flow.why,
    route: withDecisionQuery(flow.next, { from: key, step: flow.step }),
    cta: flow.cta,
    step: flow.step,
    chainIndex: Math.max(0, idx),
  };
}

/** Primary CEO next step from Morning Brief tone — minimizes clicks. */
export function deriveCeoPrimaryAction(opts: {
  tone: "calm" | "watch" | "alert";
  unread: number;
  healthBad: boolean;
}): { route: string; cta: string; why: string; step: DecisionStep } {
  if (opts.tone === "alert" || opts.healthBad) {
    return {
      route: "/platform-builder/control-tower",
      cta: "Resolve Attention now",
      why: "Critical signals need an owner decision first",
      step: "decide",
    };
  }
  if (opts.tone === "watch" || opts.unread > 0) {
    return {
      route: "/platform-builder/mission-control",
      cta: "Review live ops",
      why: "Confirm health before new initiatives",
      step: "understand",
    };
  }
  return {
    route: "/enterprise-city",
    cta: "Scan the company map",
    why: "Calm day — use City for opportunity glance",
    step: "observe",
  };
}

/** Concrete CTA labels — avoid abstract “Open”. */
export const CTA = {
  kpi: {
    sales: "Review revenue pulse",
    clients: "Inspect client base",
    deals: "Work open deals",
    processes: "Check active processes",
    automation: "Review AI automation",
    documents: "Open documents",
  } as Record<string, string>,
  quick: {
    control_tower: "Decide escalations",
    mission_control: "Check live health",
    ai_concierge: "Ask Advisor to prioritize",
    ai_team: "Review running agents",
    enterprise_city: "Glance company map",
    digital_twin: "Inspect Twin structure",
  } as Record<string, string>,
} as const;

export function rememberNavDecision(from: string, to: string, label: string, step: DecisionStep = "act") {
  const flow = CROSS_MODULE_FLOW[pathKey(to)];
  pushDecisionContext({
    from: pathKey(from),
    step,
    label,
    nextRoute: flow?.next || "/dashboard?mode=executive",
    nextCta: flow?.cta || "Return to Morning Brief",
    focus: pathKey(to),
  });
}

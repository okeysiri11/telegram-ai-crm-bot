/**
 * Enterprise Intelligence Runtime — Sprint 29.7.
 * Advisory insights & recommendations only — never auto-executes.
 */

import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { interactionRuntime } from "@/runtime/interactionRuntime";
import { cityVisualizationRuntime } from "@/runtime/cityVisualization";
import { spatialRuntime } from "@/runtime/spatialRuntime";
import { lifeEngine } from "@/runtime/lifeEngine";
import { businessNetworkEngine } from "@/runtime/businessNetwork";
import { digitalCitizenEngine } from "@/runtime/digitalCitizen";
import { assetRuntime } from "@/runtime/assetRuntime";
import { workflowRuntime } from "@/runtime/workflowRuntime";
import { automationEngine } from "@/runtime/automation";
import {
  INTELLIGENCE_RUNTIME_VERSION,
  type IntelligenceCycleResult,
  type RecommendationAudience,
  type RiskKind,
  type InsightCategory,
} from "./intelligenceTypes";
import { intelligenceEvents } from "./intelligenceEvents";
import { intelligenceCache } from "./intelligenceCache";
import { collectLiveSignals } from "./liveSignals";
import { patternDetector } from "./patternDetector";
import { trendAnalyzer } from "./trendAnalyzer";
import { riskDetector } from "./riskDetector";
import { insightEngine, buildAnalytics } from "./insightEngine";
import { recommendationEngine } from "./recommendationEngine";

let booted = false;
let analyzing = false;
let busUnsub: (() => void) | null = null;
let bgTimer: ReturnType<typeof setInterval> | null = null;
let revision = 0;

function registerCommands() {
  commandRuntime.register({
    id: "intelligence_open",
    action: "open_intelligence_runtime",
    label: "Open Intelligence Runtime",
    kind: "navigate",
    keywords: ["intelligence", "insight", "recommendation", "risk", "advisory"],
    route: "/intelligence",
    permission: "*",
  });
  commandRuntime.register({
    id: "intelligence_analyze",
    action: "run_intelligence_cycle",
    label: "Run Intelligence Cycle",
    kind: "system",
    keywords: ["analyze", "insights", "advisory"],
    permission: "*",
    handler: async () => {
      const cycle = intelligenceRuntime.analyze({ force: true });
      return {
        ok: true,
        message: `rev ${cycle.revision} · ${cycle.insights.length} insights · ${cycle.recommendations.length} recs (advisory)`,
      };
    },
  });
}

function subscribeBuses() {
  busUnsub?.();
  busUnsub = enterpriseEventBus.subscribe((event) => {
    if (!booted || analyzing) return;
    const t = event.type;
    if (
      t === "life_engine_update" ||
      t === "workflow_update" ||
      t === "asset_runtime_update" ||
      t === "business_network_update" ||
      t === "interaction_runtime_update" ||
      t === "city_visualization_update"
    ) {
      // Background incremental refresh — still advisory only
      intelligenceRuntime.analyze();
    }
  });
}

function startBackground() {
  if (bgTimer) return;
  bgTimer = setInterval(() => {
    if (!booted || analyzing) return;
    intelligenceRuntime.analyze();
  }, 15_000);
}

function stopBackground() {
  if (bgTimer) {
    clearInterval(bgTimer);
    bgTimer = null;
  }
}

export const intelligenceRuntime = {
  version: INTELLIGENCE_RUNTIME_VERSION,

  /** Explicit: this runtime never executes recommendations autonomously */
  policy: {
    autonomousExecution: false,
    recommendationsRequireApproval: true,
    advisoryOnly: true,
  } as const,

  startup() {
    if (booted) return this.stats();
    commandRuntime.startup();
    workflowRuntime.startup();
    automationEngine.startup();
    businessNetworkEngine.startup();
    digitalCitizenEngine.startup();
    lifeEngine.startup();
    assetRuntime.startup();
    spatialRuntime.startup();
    cityVisualizationRuntime.startup();
    interactionRuntime.startup();
    intelligenceCache.clear();
    trendAnalyzer.clear();
    intelligenceEvents.clear();
    registerCommands();
    subscribeBuses();
    this.analyze({ force: true });
    startBackground();
    booted = true;
    enterpriseEventBus.publish({
      type: "runtime_update",
      source: "system",
      payload: {
        stream: "intelligence_runtime",
        ready: true,
        version: INTELLIGENCE_RUNTIME_VERSION,
        advisory: true,
        autonomousExecution: false,
      },
    });
    return this.stats();
  },

  isReady() {
    return booted;
  },

  /**
   * Run analysis cycle. Incremental via fingerprint cache.
   * Never executes recommendations or mutates operational workflows.
   */
  analyze(opts?: { force?: boolean }): IntelligenceCycleResult {
    if (!booted && !opts?.force) {
      this.startup();
      return intelligenceCache.getCycle()!;
    }
    if (analyzing) {
      return (
        intelligenceCache.getCycle() || {
          revision,
          insights: [],
          recommendations: [],
          risks: [],
          trends: [],
          patterns: [],
          analytics: buildAnalytics(collectLiveSignals(), [], 0, 0),
          at: new Date().toISOString(),
        }
      );
    }
    analyzing = true;
    try {
      const signals = collectLiveSignals();
      if (!opts?.force && intelligenceCache.fingerprintValid(signals.fingerprint)) {
        return intelligenceCache.getCycle()!;
      }
      revision += 1;
      const patterns = patternDetector.detect(signals);
      const trends = trendAnalyzer.analyze(signals);
      const risks = riskDetector.detect(signals);
      const insights = insightEngine.generate(signals, risks, patterns);
      const recommendations = recommendationEngine.generate(signals, insights, risks);
      const analytics = buildAnalytics(signals, risks, insights.length, recommendations.length);
      const cycle: IntelligenceCycleResult = {
        revision,
        insights,
        recommendations,
        risks,
        trends,
        patterns,
        analytics,
        at: new Date().toISOString(),
      };
      intelligenceCache.putCycle(cycle, signals.fingerprint);
      intelligenceCache.bumpAggregation("cycles");
      return cycle;
    } finally {
      analyzing = false;
    }
  },

  cycle() {
    if (!booted) this.startup();
    return intelligenceCache.getCycle() || this.analyze({ force: true });
  },

  insights(category?: InsightCategory) {
    const all = this.cycle().insights;
    return category ? all.filter((i) => i.category === category) : all;
  },

  recommendations(audience?: RecommendationAudience) {
    const all = this.cycle().recommendations;
    return audience ? all.filter((r) => r.audience === audience) : all;
  },

  risks(kind?: RiskKind) {
    const all = this.cycle().risks;
    return kind ? all.filter((r) => r.kind === kind) : all;
  },

  trends() {
    return this.cycle().trends;
  },

  patterns() {
    return this.cycle().patterns;
  },

  analytics() {
    return this.cycle().analytics;
  },

  /**
   * Explicitly blocked: intelligence must not execute.
   * Use Interaction Runtime / Workflow with user approval instead.
   */
  executeRecommendation(_recommendationId: string): {
    ok: false;
    error: "autonomous_execution_forbidden";
    message: string;
  } {
    return {
      ok: false,
      error: "autonomous_execution_forbidden",
      message:
        "Enterprise Intelligence is advisory only. Use Interaction Runtime or Workflow with explicit approval.",
    };
  },

  events: intelligenceEvents,
  cache: intelligenceCache,

  stats() {
    if (!booted) this.startup();
    const c = this.cycle();
    return {
      version: INTELLIGENCE_RUNTIME_VERSION,
      advisoryOnly: true,
      autonomousExecution: false,
      revision: c.revision,
      insights: c.insights.length,
      recommendations: c.recommendations.length,
      risks: c.risks.length,
      trends: c.trends.length,
      patterns: c.patterns.length,
      analytics: c.analytics,
      cache: intelligenceCache.stats(),
      events: intelligenceEvents.list(200).length,
      cycles: intelligenceCache.getAggregation("cycles"),
    };
  },

  inspectorSnapshot() {
    if (!booted) this.startup();
    const c = this.cycle();
    return {
      version: INTELLIGENCE_RUNTIME_VERSION,
      policy: this.policy,
      cycle: c,
      stats: this.stats(),
      events: intelligenceEvents.list(30),
      byAudience: {
        owner: this.recommendations("owner"),
        manager: this.recommendations("manager"),
        partner: this.recommendations("partner"),
        asset: this.recommendations("asset"),
      },
    };
  },

  __resetForTests() {
    stopBackground();
    busUnsub?.();
    busUnsub = null;
    intelligenceCache.clear();
    trendAnalyzer.clear();
    intelligenceEvents.clear();
    revision = 0;
    analyzing = false;
    booted = false;
  },
};

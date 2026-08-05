/**
 * Risk detection — Sprint 29.7 (advisory only).
 */

import type { EnterpriseRisk } from "./intelligenceTypes";
import type { LiveSignals } from "./liveSignals";
import { publishIntelligenceEvent } from "./intelligenceEvents";

function uid() {
  return `risk_${Math.random().toString(36).slice(2, 10)}`;
}

function now() {
  return new Date().toISOString();
}

export const riskDetector = {
  detect(signals: LiveSignals): EnterpriseRisk[] {
    const risks: EnterpriseRisk[] = [];

    if (signals.automationPending >= 3 || signals.workflowRunning >= 3) {
      risks.push({
        id: uid(),
        kind: "process_delay",
        title: "Process queue pressure",
        detail: `${signals.automationPending} automation jobs pending · ${signals.workflowRunning} workflows running`,
        severity: signals.automationPending >= 5 ? "high" : "medium",
        subjectIds: [],
        mitigationHint: "Review automation queue and workflow sessions (approval required)",
        createdAt: now(),
      });
    }

    const idle = signals.assetsTotal - signals.assetsInUse - signals.assetsMaintenance;
    if (idle >= 3 && signals.assetsTotal > 0) {
      risks.push({
        id: uid(),
        kind: "idle_asset",
        title: "Idle assets detected",
        detail: `${Math.max(0, idle)} assets appear unused`,
        severity: idle >= 6 ? "medium" : "low",
        subjectIds: [],
        mitigationHint: "Consider reassignment via Asset Runtime (manual approval)",
        createdAt: now(),
      });
    }

    for (const hot of signals.occupancyHot.filter((h) => h.count >= 4)) {
      risks.push({
        id: uid(),
        kind: "overloaded_employee",
        title: `High occupancy at ${hot.buildingId}`,
        detail: `${hot.count} occupants — possible overload`,
        severity: hot.count >= 8 ? "high" : "medium",
        subjectIds: [hot.buildingId],
        mitigationHint: "Redistribute meetings or staff (requires manager approval)",
        createdAt: now(),
      });
    }

    if (signals.workflowFailed > 0) {
      risks.push({
        id: uid(),
        kind: "workflow_failure",
        title: "Workflow failures observed",
        detail: `${signals.workflowFailed} failed workflow history entries`,
        severity: signals.workflowFailed >= 3 ? "high" : "medium",
        subjectIds: [],
        mitigationHint: "Inspect Workflow Runtime history — do not auto-retry without approval",
        createdAt: now(),
      });
    }

    if (signals.partnersPending > 0) {
      risks.push({
        id: uid(),
        kind: "missing_approval",
        title: "Partner approvals pending",
        detail: `${signals.partnersPending} relationship(s) awaiting approval`,
        severity: signals.partnersPending >= 2 ? "medium" : "low",
        subjectIds: [],
        mitigationHint: "Review Business Network pending relationships",
        createdAt: now(),
      });
    }

    if (signals.assetsMaintenance > 0) {
      risks.push({
        id: uid(),
        kind: "operational",
        title: "Assets in maintenance",
        detail: `${signals.assetsMaintenance} asset(s) under maintenance`,
        severity: "low",
        subjectIds: [],
        mitigationHint: "Track maintenance completion in Asset Runtime",
        createdAt: now(),
      });
    }

    if (signals.automationFailed > 0) {
      risks.push({
        id: uid(),
        kind: "operational",
        title: "Automation failures",
        detail: `${signals.automationFailed} failed automation history entries`,
        severity: signals.automationFailed >= 2 ? "medium" : "low",
        subjectIds: [],
        mitigationHint: "Review Automation Engine history before re-running",
        createdAt: now(),
      });
    }

    for (const r of risks) {
      publishIntelligenceEvent("RiskDetected", {
        riskId: r.id,
        kind: r.kind,
        severity: r.severity,
      });
    }
    return risks;
  },
};

/**
 * Pattern detector — Sprint 29.7 (advisory).
 */

import type { DetectedPattern } from "./intelligenceTypes";
import type { LiveSignals } from "./liveSignals";
import { publishIntelligenceEvent } from "./intelligenceEvents";

function uid() {
  return `pat_${Math.random().toString(36).slice(2, 10)}`;
}

function now() {
  return new Date().toISOString();
}

export const patternDetector = {
  detect(signals: LiveSignals): DetectedPattern[] {
    const patterns: DetectedPattern[] = [];

    if (signals.meetingsActive > 0 && signals.occupancyHot.length > 0) {
      patterns.push({
        id: uid(),
        name: "meeting_occupancy_cluster",
        description: "Active meetings correlate with occupied buildings",
        confidence: Math.min(0.95, 0.55 + signals.meetingsActive * 0.1),
        evidence: [
          `active_meetings=${signals.meetingsActive}`,
          `hot_buildings=${signals.occupancyHot.slice(0, 3).map((h) => h.buildingId).join(",")}`,
        ],
        category: "citizen",
        createdAt: now(),
      });
    }

    if (signals.assetsMaintenance > 0 && signals.assetsAvailable / Math.max(1, signals.assetsTotal) < 0.5) {
      patterns.push({
        id: uid(),
        name: "asset_pressure",
        description: "Maintenance load coincides with low asset availability",
        confidence: 0.7,
        evidence: [
          `maintenance=${signals.assetsMaintenance}`,
          `available=${signals.assetsAvailable}/${signals.assetsTotal}`,
        ],
        category: "asset",
        createdAt: now(),
      });
    }

    if (signals.partnersPending > 0 && signals.partnersApproved > 0) {
      patterns.push({
        id: uid(),
        name: "partner_pipeline",
        description: "Partner network has pending approvals alongside active relations",
        confidence: 0.65,
        evidence: [`pending=${signals.partnersPending}`, `approved=${signals.partnersApproved}`],
        category: "partner",
        createdAt: now(),
      });
    }

    if (signals.workflowFailed > 0 || signals.automationFailed > 0) {
      patterns.push({
        id: uid(),
        name: "execution_friction",
        description: "Workflow/automation failures form an operational friction pattern",
        confidence: Math.min(0.9, 0.5 + (signals.workflowFailed + signals.automationFailed) * 0.1),
        evidence: [
          `wf_failed=${signals.workflowFailed}`,
          `auto_failed=${signals.automationFailed}`,
        ],
        category: "workflow",
        createdAt: now(),
      });
    }

    const busyDistricts = signals.districtActivity.filter((d) => d.activity >= 40);
    if (busyDistricts.length >= 2) {
      patterns.push({
        id: uid(),
        name: "multi_district_pulse",
        description: "Multiple districts show elevated activity",
        confidence: 0.6,
        evidence: busyDistricts.slice(0, 4).map((d) => `${d.districtId}:${d.activity}`),
        category: "district",
        createdAt: now(),
      });
    }

    for (const p of patterns) {
      publishIntelligenceEvent("PatternDetected", {
        patternId: p.id,
        name: p.name,
        confidence: p.confidence,
      });
    }
    return patterns;
  },
};

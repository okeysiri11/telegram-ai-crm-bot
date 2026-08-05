/**
 * Live analytics signals from real runtimes — Sprint 29.7.
 * Read-only aggregation; never mutates business state.
 */

import { lifeEngine } from "@/runtime/lifeEngine";
import { digitalCitizenEngine } from "@/runtime/digitalCitizen";
import { businessNetworkEngine } from "@/runtime/businessNetwork";
import { assetRuntime } from "@/runtime/assetRuntime";
import { workflowRuntime } from "@/runtime/workflowRuntime";
import { automationEngine } from "@/runtime/automation";
import { spatialRuntime } from "@/runtime/spatialRuntime";
import { cityVisualizationRuntime } from "@/runtime/cityVisualization";
import { interactionRuntime } from "@/runtime/interactionRuntime";

export type LiveSignals = {
  fingerprint: string;
  citizensOnline: number;
  citizensTotal: number;
  meetingsActive: number;
  meetingsScheduled: number;
  occupancyHot: { buildingId: string; count: number }[];
  assetsTotal: number;
  assetsAvailable: number;
  assetsMaintenance: number;
  assetsInUse: number;
  partnersPending: number;
  partnersApproved: number;
  profiles: number;
  workflowRunning: number;
  workflowFailed: number;
  workflowCompleted: number;
  automationFailed: number;
  automationPending: number;
  projects: { id: string; name: string; members: number }[];
  districtActivity: { districtId: string; activity: number; population: number }[];
  selectionCount: number;
  interactionActions: number;
  spatialBuildings: number;
};

export function collectLiveSignals(): LiveSignals {
  lifeEngine.startup();
  digitalCitizenEngine.startup();
  businessNetworkEngine.startup();
  assetRuntime.startup();
  workflowRuntime.startup();
  automationEngine.startup();
  spatialRuntime.startup();
  cityVisualizationRuntime.startup();
  interactionRuntime.startup();

  const citizens = digitalCitizenEngine.listCitizens();
  const online = citizens.filter((c) =>
    ["online", "busy", "meeting", "working"].includes(c.presence.status),
  ).length;

  const meetings = lifeEngine.meetings.list();
  const occupancy = lifeEngine.occupancy();
  const occupancyHot = occupancy
    .map((o) => ({ buildingId: o.buildingId, count: o.occupants.length }))
    .filter((o) => o.count > 0)
    .sort((a, b) => b.count - a.count);

  const assets = assetRuntime.list();
  const rels = businessNetworkEngine.listRelationships();
  const sessions = workflowRuntime.listSessions();
  const hist = workflowRuntime.history(40);
  const autoHist = automationEngine.history(30);
  const autoQueue = automationEngine.listQueue();

  const projects = lifeEngine.cityRuntime().projects.map((p) => ({
    id: p.projectId,
    name: p.projectName,
    members: p.memberCount,
  }));

  const districts = cityVisualizationRuntime.scene().districts.map((d) => ({
    districtId: d.districtId,
    activity: d.activity,
    population: d.population,
  }));

  const fingerprint = [
    online,
    meetings.length,
    assets.length,
    rels.length,
    sessions.length,
    hist.length,
    autoHist.length,
    projects.length,
    districts.map((d) => `${d.districtId}:${d.activity}`).join("|"),
    interactionRuntime.stats().history,
  ].join("::");

  return {
    fingerprint,
    citizensOnline: online,
    citizensTotal: citizens.length,
    meetingsActive: meetings.filter((m) => m.status === "active").length,
    meetingsScheduled: meetings.filter((m) => m.status === "scheduled").length,
    occupancyHot,
    assetsTotal: assets.length,
    assetsAvailable: assets.filter((a) => a.available).length,
    assetsMaintenance: assets.filter((a) => a.status === "maintenance").length,
    assetsInUse: assets.filter((a) => a.status === "in_use" || a.status === "assigned").length,
    partnersPending: rels.filter((r) => r.state === "pending").length,
    partnersApproved: rels.filter((r) => r.state === "approved").length,
    profiles: businessNetworkEngine.listProfiles().length,
    workflowRunning: sessions.filter((s) => s.status === "running").length,
    workflowFailed: hist.filter((h) => h.status === "failed").length,
    workflowCompleted: hist.filter((h) => h.status === "completed").length,
    automationFailed: autoHist.filter((h) => h.status === "failed").length,
    automationPending: autoQueue.filter((j) => j.status === "pending" || j.status === "waiting").length,
    projects,
    districtActivity: districts,
    selectionCount: interactionRuntime.selection().targets.length,
    interactionActions: interactionRuntime.history(100).filter((h) => h.event === "action").length,
    spatialBuildings: spatialRuntime.list("building").length,
  };
}

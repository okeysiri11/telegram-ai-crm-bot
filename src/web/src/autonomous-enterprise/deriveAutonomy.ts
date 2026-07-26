/**
 * Autonomous Enterprise derivation — Sprint 33.5.
 * Pure client layer over Runtime / Predictive / EI + local approval state.
 * No new AI Core / Automation Engine / Runtime Engine.
 */

import type { LiveEnterpriseSnapshot } from "@/live-ops";
import type { AppNotification } from "@/notifications/notificationStore";
import { deriveRuntime } from "@/ai-runtime/deriveRuntime";
import { derivePredictive } from "@/predictive-intelligence/derivePredictive";
import { deriveIntelligence } from "@/enterprise-intelligence/deriveIntelligence";
import {
  AUTONOMY_LEVELS,
  APPROVAL_CATEGORIES,
  CRITICAL_ACTIONS,
  levelLabel,
  type AutonomyLevel,
  type ApprovalCategory,
} from "./autonomyCatalog";
import {
  getAutonomyLevel,
  listApprovals,
  listJournal,
  type ApprovalItem,
  type JournalEntry,
} from "./autonomyState";

export type AutonomyDashboard = {
  level: AutonomyLevel;
  levelTitle: string;
  activeAutonomous: number;
  awaitingApproval: number;
  completedAuto: number;
  needsIntervention: number;
};

export type GovernanceStats = {
  aiDecisions: number;
  userApproved: number;
  userRejected: number;
  timeSavedMin: number;
  byDepartment: Array<{ id: ApprovalCategory | string; label: string; autonomyPct: number }>;
};

export type TwinAutonomyView = {
  autonomousProcesses: string[];
  pendingApprovals: string[];
  criticalDecisions: string[];
  departmentLevels: Array<{ label: string; level: AutonomyLevel }>;
};

export type AutonomyBundle = {
  dashboard: AutonomyDashboard;
  approvals: ApprovalItem[];
  journal: JournalEntry[];
  governance: GovernanceStats;
  twin: TwinAutonomyView;
  criticalActions: readonly string[];
  levels: typeof AUTONOMY_LEVELS;
  categories: typeof APPROVAL_CATEGORIES;
};

export function deriveAutonomy(
  snapshot: LiveEnterpriseSnapshot,
  opts: { roleId?: string; notifications?: AppNotification[]; tick?: number } = {},
): AutonomyBundle {
  void opts.tick;
  const notifications = opts.notifications || [];
  const level = getAutonomyLevel(opts.roleId);
  const runtime = deriveRuntime(snapshot, notifications);
  const pred = derivePredictive(snapshot, notifications);
  const intel = deriveIntelligence(snapshot, notifications);
  const approvals = listApprovals();
  const journal = listJournal();

  const pending = approvals.filter((a) => a.status === "pending");
  const approved = approvals.filter((a) => a.status === "approved" || a.status === "edited");
  const rejected = approvals.filter((a) => a.status === "rejected");

  const autoJournal = journal.filter((j) => j.userConfirmation === "auto");
  const activeAutonomous =
    level >= 2
      ? runtime.counts.active + Math.min(2, autoJournal.length)
      : 0;

  const criticalPending = pending.filter((a) => a.risk === "critical" || a.risk === "high").length;

  const dashboard: AutonomyDashboard = {
    level,
    levelTitle: levelLabel(level),
    activeAutonomous,
    awaitingApproval: pending.length + runtime.counts.paused,
    completedAuto: autoJournal.length + (level >= 2 ? runtime.counts.completed : 0),
    needsIntervention: criticalPending + (runtime.health.needsIntervention ? 1 : 0) + runtime.counts.failed,
  };

  const userApproved = approved.length + journal.filter((j) => j.userConfirmation === "approved").length;
  const userRejected = rejected.length + journal.filter((j) => j.userConfirmation === "rejected").length;
  const aiDecisions = autoJournal.length + (level >= 2 ? runtime.counts.completed : 0) + approved.length;

  const byDepartment = APPROVAL_CATEGORIES.map((c) => {
    const catItems = approvals.filter((a) => a.category === c.id);
    const done = catItems.filter((a) => a.status !== "pending").length;
    const base = level * 18 + (done ? 10 : 0) + (c.id === "crm" && snapshot.activeModules.includes("crm") ? 8 : 0);
    return {
      id: c.id,
      label: c.label,
      autonomyPct: Math.min(95, base + (catItems.length ? 5 : 0)),
    };
  });

  const governance: GovernanceStats = {
    aiDecisions,
    userApproved,
    userRejected,
    timeSavedMin: aiDecisions * 4 + userApproved * 2,
    byDepartment,
  };

  const twin: TwinAutonomyView = {
    autonomousProcesses:
      level >= 2
        ? runtime.twin.processesRunning.concat(autoJournal.slice(0, 2).map((j) => j.action)).slice(0, 6)
        : ["Manual mode — no auto processes"],
    pendingApprovals: pending.map((a) => a.title).slice(0, 6),
    criticalDecisions: pending
      .filter((a) => a.risk === "critical" || a.risk === "high")
      .map((a) => a.title)
      .concat(pred.executive.risingRisks.slice(0, 2))
      .slice(0, 6),
    departmentLevels: byDepartment.map((d) => ({
      label: d.label,
      level: (Math.min(4, Math.max(0, Math.round(d.autonomyPct / 25))) as AutonomyLevel),
    })),
  };

  void intel;

  return {
    dashboard,
    approvals,
    journal: journal.slice(0, 20),
    governance,
    twin,
    criticalActions: CRITICAL_ACTIONS,
    levels: AUTONOMY_LEVELS,
    categories: APPROVAL_CATEGORIES,
  };
}

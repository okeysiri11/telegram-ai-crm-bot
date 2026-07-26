/**
 * Autonomy persistence — Sprint 33.5.
 * localStorage (same pattern as Marketplace / Integration Hub).
 * No new Store library / Engine.
 */

import type { ApprovalCategory, ApprovalStatus, AutonomyLevel, RiskLevel } from "./autonomyCatalog";
import { resolveDefaultLevel } from "./autonomyCatalog";

const LEVEL_KEY = "ewp_autonomy_level_v1";
const APPROVAL_KEY = "ewp_autonomy_approvals_v1";
const JOURNAL_KEY = "ewp_autonomy_journal_v1";

export type ApprovalItem = {
  id: string;
  category: ApprovalCategory;
  title: string;
  recommendation: string;
  reason: string;
  risk: RiskLevel;
  status: ApprovalStatus;
  aiAgent: string;
  workflow: string;
  createdAt: string;
  decidedAt?: string;
  decidedBy?: string;
};

export type JournalEntry = {
  id: string;
  at: string;
  initiator: string;
  aiAgent: string;
  workflow: string;
  action: string;
  result: string;
  userConfirmation: "approved" | "rejected" | "edited" | "auto" | "pending";
  category: ApprovalCategory | "system";
};

function readJson<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function writeJson(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* ignore */
  }
}

export function getAutonomyLevel(roleId?: string): AutonomyLevel {
  const stored = readJson<{ level?: AutonomyLevel }>(LEVEL_KEY, {});
  if (typeof stored.level === "number" && stored.level >= 0 && stored.level <= 4) {
    return stored.level as AutonomyLevel;
  }
  return resolveDefaultLevel(roleId);
}

export function setAutonomyLevel(level: AutonomyLevel) {
  writeJson(LEVEL_KEY, { level, updatedAt: new Date().toISOString() });
}

function seedApprovals(): ApprovalItem[] {
  const existing = readJson<ApprovalItem[]>(APPROVAL_KEY, []);
  if (existing.length) return existing;
  const now = new Date().toISOString();
  const seed: ApprovalItem[] = [
    {
      id: "ap_crm_1",
      category: "crm",
      title: "Qualify 12 leads as Hot",
      recommendation: "Approve mass stage update for high-score leads",
      reason: "Predictive client activity ↑ · Sales Ops queue ready",
      risk: "medium",
      status: "pending",
      aiAgent: "Sales Specialist",
      workflow: "Lead intake",
      createdAt: now,
    },
    {
      id: "ap_fin_1",
      category: "finance",
      title: "Release payment batch €4.2k",
      recommendation: "Hold for CFO confirmation",
      reason: "Amount above low-risk threshold",
      risk: "critical",
      status: "pending",
      aiAgent: "Finance Agent",
      workflow: "Invoice approval",
      createdAt: now,
    },
    {
      id: "ap_legal_1",
      category: "legal",
      title: "Send NDA to Acme Ltd",
      recommendation: "Approve after clause check",
      reason: "Legal template matched · Knowledge OK",
      risk: "high",
      status: "pending",
      aiAgent: "Legal Specialist",
      workflow: "Contract send",
      createdAt: now,
    },
    {
      id: "ap_doc_1",
      category: "documents",
      title: "Archive 8 expired policies",
      recommendation: "Auto-archive (low risk)",
      reason: "Documents older than retention policy",
      risk: "low",
      status: "pending",
      aiAgent: "Knowledge Agent",
      workflow: "Doc intake",
      createdAt: now,
    },
    {
      id: "ap_ai_1",
      category: "ai_team",
      title: "Scale Sales Ops concurrency +1",
      recommendation: "Approve temporary scale",
      reason: "Runtime queue forecast rising",
      risk: "medium",
      status: "pending",
      aiAgent: "Concierge",
      workflow: "AI Team policy",
      createdAt: now,
    },
    {
      id: "ap_wf_1",
      category: "workflow",
      title: "Enable auto-follow-up Workflow",
      recommendation: "Enable for CRM stage Won",
      reason: "Opportunity detection · unused automation",
      risk: "low",
      status: "pending",
      aiAgent: "Ops Copilot",
      workflow: "Follow-up automation",
      createdAt: now,
    },
  ];
  writeJson(APPROVAL_KEY, seed);
  return seed;
}

export function listApprovals(): ApprovalItem[] {
  return seedApprovals();
}

export function decideApproval(
  id: string,
  status: Exclude<ApprovalStatus, "pending">,
  decidedBy = "User",
): ApprovalItem | null {
  const list = seedApprovals();
  const idx = list.findIndex((a) => a.id === id);
  if (idx < 0) return null;
  const item = {
    ...list[idx]!,
    status,
    decidedAt: new Date().toISOString(),
    decidedBy,
  };
  list[idx] = item;
  writeJson(APPROVAL_KEY, list);
  appendJournal({
    id: `j_${id}_${status}`,
    at: item.decidedAt!,
    initiator: item.aiAgent,
    aiAgent: item.aiAgent,
    workflow: item.workflow,
    action: item.title,
    result: status,
    userConfirmation: status,
    category: item.category,
  });
  return item;
}

export function listJournal(): JournalEntry[] {
  const j = readJson<JournalEntry[]>(JOURNAL_KEY, []);
  if (j.length) return j;
  const seed: JournalEntry[] = [
    {
      id: "j_seed_1",
      at: new Date(Date.now() - 3600_000).toISOString(),
      initiator: "Concierge",
      aiAgent: "Ops Concierge",
      workflow: "Daily brief",
      action: "Publish morning brief",
      result: "completed",
      userConfirmation: "auto",
      category: "ai_team",
    },
    {
      id: "j_seed_2",
      at: new Date(Date.now() - 7200_000).toISOString(),
      initiator: "Sales Specialist",
      aiAgent: "Sales Specialist",
      workflow: "Lead intake",
      action: "Auto-tag lead source",
      result: "completed",
      userConfirmation: "auto",
      category: "crm",
    },
  ];
  writeJson(JOURNAL_KEY, seed);
  return seed;
}

export function appendJournal(entry: JournalEntry) {
  const j = listJournal();
  j.unshift(entry);
  writeJson(JOURNAL_KEY, j.slice(0, 80));
}

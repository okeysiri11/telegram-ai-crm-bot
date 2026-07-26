/**
 * Enterprise Governance, Compliance & Security derivation — Sprint 33.9.
 * Composition over Autonomy approvals, RBAC hints, Runtime, EI, Integrations, Fabric.
 * No new RBAC / Security / Audit / Policy / Approval Engine.
 */

import type { LiveEnterpriseSnapshot } from "@/live-ops";
import type { AppNotification } from "@/notifications/notificationStore";
import { deriveRuntime } from "@/ai-runtime/deriveRuntime";
import { derivePredictive } from "@/predictive-intelligence/derivePredictive";
import { deriveIntelligence } from "@/enterprise-intelligence/deriveIntelligence";
import { deriveIntegrationHub } from "@/enterprise-integrations/deriveIntegrations";
import { deriveDataFabric } from "@/enterprise-data-fabric/deriveFabric";
import { deriveAutonomy } from "@/autonomous-enterprise/deriveAutonomy";
import { listApprovals, listJournal, type ApprovalItem } from "@/autonomous-enterprise/autonomyState";
import { ENTERPRISE_POLICIES, matchPolicy, type EnterprisePolicy } from "./policiesCatalog";

export type PolicyHealth = EnterprisePolicy & {
  status: "healthy" | "watch" | "breach";
  openIssues: number;
  detail: string;
};

export type ValidationStep = {
  id: "policy" | "permission" | "approval" | "execution";
  label: string;
  status: "pass" | "block" | "pending" | "skip";
  detail: string;
};

export type PolicyValidation = {
  actionId: string;
  actionTitle: string;
  steps: ValidationStep[];
  allowed: boolean;
  blockedBy?: string;
};

export type ExecApprovalRow = {
  id: string;
  title: string;
  queue: "pending" | "approved" | "rejected" | "expired" | "critical";
  category: string;
  risk: string;
  aiAgent: string;
  createdAt: string;
  detail: string;
};

export type AuditEvent = {
  id: string;
  who: string;
  what: string;
  when: string;
  why: string;
  source: "ai" | "human" | "workflow" | "api";
};

export type RiskCard = {
  id: string;
  kind: "security" | "compliance" | "operational" | "ai" | "integration";
  label: string;
  score: number;
  tone: "ok" | "warn" | "risk";
  detail: string;
};

export type AiGovernanceRow = {
  id: string;
  name: string;
  permissions: string[];
  autonomyLevel: number;
  lastDecisions: string[];
  policyViolations: number;
  confidence: number;
  humanOverrides: number;
};

export type ComplianceScores = {
  auditScore: number;
  securityScore: number;
  compliancePct: number;
  policyHealth: number;
};

export type GovernanceBundle = {
  policies: PolicyHealth[];
  validations: PolicyValidation[];
  approvalQueue: ExecApprovalRow[];
  auditTimeline: AuditEvent[];
  risks: RiskCard[];
  aiGovernance: AiGovernanceRow[];
  compliance: ComplianceScores;
};

function clamp(n: number, min = 0, max = 100) {
  return Math.max(min, Math.min(max, n));
}

function hash(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

function isExpired(item: ApprovalItem): boolean {
  if (item.status !== "pending") return false;
  const t = Date.parse(item.createdAt);
  if (Number.isNaN(t)) return false;
  return Date.now() - t > 7 * 86_400_000;
}

function permissionOk(roleId: string | undefined, policy: EnterprisePolicy, perms: string[]): boolean {
  const r = (roleId || "").toLowerCase();
  if (r.includes("owner") || r.includes("admin") || perms.includes("admin") || perms.includes("platform_owner")) {
    return true;
  }
  if (policy.domain === "operations" && (perms.includes("write") || perms.includes("read"))) return true;
  if (policy.severity === "critical") return r.includes("manager") || perms.includes("write");
  return perms.includes("write") || perms.includes("read");
}

export function deriveGovernance(
  snapshot: LiveEnterpriseSnapshot,
  opts: {
    notifications?: AppNotification[];
    roleId?: string;
    permissions?: string[];
  } = {},
): GovernanceBundle {
  const notifications = opts.notifications || [];
  const roleId = opts.roleId;
  const perms = opts.permissions?.length ? opts.permissions : ["read", "write"];

  const runtime = deriveRuntime(snapshot, notifications);
  const pred = derivePredictive(snapshot, notifications);
  const intel = deriveIntelligence(snapshot, notifications);
  const intHub = deriveIntegrationHub(snapshot);
  const fabric = deriveDataFabric(snapshot, { notifications });
  const autonomy = deriveAutonomy(snapshot, { roleId, notifications });

  const approvals = listApprovals();
  const journal = listJournal();

  const pending = approvals.filter((a) => a.status === "pending");
  const failed = runtime.counts.failed + snapshot.aiOps.errors.length;
  const highRisks = pred.risks.filter((r) => r.severity === "high").length;

  const policies: PolicyHealth[] = ENTERPRISE_POLICIES.map((p) => {
    const related = approvals.filter((a) => p.tokens.test(a.title + a.reason + a.category));
    const open = related.filter((a) => a.status === "pending" && (a.risk === "high" || a.risk === "critical")).length;
    let status: PolicyHealth["status"] = "healthy";
    if (open > 0 || (p.domain === "security" && intHub.dashboard.errors > 0)) status = "watch";
    if (
      (p.domain === "operations" && failed > 1) ||
      (p.domain === "ai_usage" && highRisks > 1) ||
      (p.domain === "privacy" && fabric.executive.missingData > 2)
    ) {
      status = "breach";
    }
    return {
      ...p,
      status,
      openIssues: open + (status === "breach" ? 1 : 0),
      detail:
        status === "breach"
          ? "Требуется remediation"
          : status === "watch"
            ? `${open || 1} open control(s)`
            : "В норме",
    };
  });

  const candidateActions = [
    ...runtime.jobs.filter((j) => j.state === "active" || j.state === "waiting" || j.state === "paused").slice(0, 4),
    ...pending.slice(0, 3).map((a) => ({
      id: a.id,
      title: a.title,
      state: "waiting" as const,
    })),
  ];

  const validations: PolicyValidation[] = candidateActions.map((action) => {
    const title = "title" in action ? action.title : String(action);
    const id = "id" in action ? action.id : `act_${hash(title)}`;
    const policy = matchPolicy(title);
    const polHealth = policies.find((x) => x.id === policy.id);
    const policyStatus: ValidationStep["status"] = polHealth?.status === "breach" ? "block" : "pass";
    const permPass = permissionOk(roleId, policy, perms);
    const needsApproval =
      policy.requiresApproval ||
      autonomy.dashboard.level < 2 ||
      /critical|payment|delete|contract/i.test(title);
    const relatedApproval = pending.find((a) => a.id === id || a.title === title);
    const approvalStatus: ValidationStep["status"] = !needsApproval
      ? "skip"
      : relatedApproval
        ? "pending"
        : autonomy.dashboard.level >= 3 && !policy.requiresApproval
          ? "pass"
          : "pending";

    const steps: ValidationStep[] = [
      {
        id: "policy",
        label: "Policy Check",
        status: policyStatus,
        detail: `${policy.label} · ${policy.summary.slice(0, 48)}`,
      },
      {
        id: "permission",
        label: "Permission Check",
        status: permPass ? "pass" : "block",
        detail: permPass ? `RBAC ok · ${policy.permissionHint}` : `Denied · need ${policy.permissionHint}`,
      },
      {
        id: "approval",
        label: "Approval Check",
        status: approvalStatus,
        detail: needsApproval
          ? relatedApproval
            ? `Pending · ${relatedApproval.aiAgent}`
            : "Requires Executive Approval"
          : "Not required at current autonomy",
      },
      {
        id: "execution",
        label: "Execution",
        status:
          policyStatus === "block" || !permPass
            ? "block"
            : approvalStatus === "pending"
              ? "pending"
              : "pass",
        detail:
          policyStatus === "block" || !permPass
            ? "Blocked"
            : approvalStatus === "pending"
              ? "Waiting approval"
              : "Ready / running",
      },
    ];

    const blocked = steps.find((s) => s.status === "block");
    return {
      actionId: id,
      actionTitle: title,
      steps,
      allowed: !blocked && approvalStatus !== "pending",
      blockedBy: blocked?.label,
    };
  });

  const approvalQueue: ExecApprovalRow[] = approvals.map((a) => {
    let queue: ExecApprovalRow["queue"] = "pending";
    if (a.status === "approved" || a.status === "edited") queue = "approved";
    else if (a.status === "rejected") queue = "rejected";
    else if (isExpired(a)) queue = "expired";
    else if (a.risk === "critical" || a.risk === "high") queue = "critical";
    else queue = "pending";
    return {
      id: a.id,
      title: a.title,
      queue,
      category: a.category,
      risk: a.risk,
      aiAgent: a.aiAgent,
      createdAt: a.createdAt,
      detail: a.reason,
    };
  });

  // Ensure all queue buckets appear
  if (!approvalQueue.some((q) => q.queue === "expired") && pending[0]) {
    approvalQueue.push({
      id: "ap_expired_demo",
      title: "Stale autonomy request",
      queue: "expired",
      category: "workflow",
      risk: "medium",
      aiAgent: "Concierge",
      createdAt: new Date(Date.now() - 10 * 86_400_000).toISOString(),
      detail: "No decision within SLA",
    });
  }

  const auditTimeline: AuditEvent[] = [
    ...journal.slice(0, 8).map((j) => ({
      id: j.id,
      who: j.userConfirmation === "auto" ? j.aiAgent : j.initiator,
      what: j.action,
      when: j.at,
      why: `${j.workflow} · ${j.result}`,
      source: (j.userConfirmation === "auto" ? "ai" : "human") as AuditEvent["source"],
    })),
    ...snapshot.activity.slice(0, 6).map((a) => ({
      id: `act_${a.id}`,
      who: a.source,
      what: a.title,
      when: a.at,
      why: a.detail || a.kind,
      source: (a.kind === "ai" || a.kind === "automation"
        ? "ai"
        : a.source === "mission_control"
          ? "api"
          : "workflow") as AuditEvent["source"],
    })),
    ...runtime.jobs.slice(0, 4).map((j) => ({
      id: `job_${j.id}`,
      who: j.executor,
      what: j.title,
      when: snapshot.updatedAt,
      why: `${j.state} · ${j.currentStep}`,
      source: "workflow" as const,
    })),
    ...notifications.slice(0, 3).map((n) => ({
      id: `notif_${n.id}`,
      who: "notification",
      what: n.title,
      when: n.createdAt,
      why: n.body || n.kind,
      source: "api" as const,
    })),
  ]
    .sort((a, b) => Date.parse(b.when) - Date.parse(a.when))
    .slice(0, 24);

  const risks: RiskCard[] = [
    {
      id: "rk_sec",
      kind: "security",
      label: "Security Risk",
      score: clamp(20 + intHub.dashboard.errors * 15 + (policies.find((p) => p.domain === "security")?.openIssues || 0) * 10),
      tone: intHub.dashboard.errors ? "risk" : "ok",
      detail: intHub.dashboard.statusSummary,
    },
    {
      id: "rk_comp",
      kind: "compliance",
      label: "Compliance Risk",
      score: clamp(15 + pending.filter((a) => a.risk === "critical").length * 20 + fabric.executive.missingData * 5),
      tone: pending.some((a) => a.risk === "critical") ? "risk" : fabric.executive.missingData ? "warn" : "ok",
      detail: `${pending.length} pending approvals · fabric missing ${fabric.executive.missingData}`,
    },
    {
      id: "rk_ops",
      kind: "operational",
      label: "Operational Risk",
      score: clamp(10 + failed * 18 + runtime.health.queueSize * 8),
      tone: failed ? "risk" : runtime.health.queueSize >= 3 ? "warn" : "ok",
      detail: `fail ${failed} · queue ${runtime.health.queueSize}`,
    },
    {
      id: "rk_ai",
      kind: "ai",
      label: "AI Risk",
      score: clamp(12 + highRisks * 15 + (4 - autonomy.dashboard.level) * 5),
      tone: highRisks ? "risk" : autonomy.dashboard.needsIntervention ? "warn" : "ok",
      detail: `Autonomy L${autonomy.dashboard.level} · intervention ${autonomy.dashboard.needsIntervention}`,
    },
    {
      id: "rk_int",
      kind: "integration",
      label: "Integration Risk",
      score: clamp(10 + intHub.dashboard.needsSetup * 8 + intHub.dashboard.errors * 12),
      tone: intHub.dashboard.errors ? "risk" : intHub.dashboard.needsSetup ? "warn" : "ok",
      detail: `${intHub.dashboard.active} active · ${intHub.dashboard.needsSetup} setup`,
    },
  ];

  const agents = [
    ...new Set(
      snapshot.aiOps.running
        .concat(snapshot.aiOps.recent)
        .concat(approvals.map((a) => a.aiAgent))
        .concat(["Concierge", "Sales Specialist", "Ops Copilot"]),
    ),
  ].slice(0, 6);

  const aiGovernance: AiGovernanceRow[] = agents.map((name, i) => {
    const agentApprovals = approvals.filter((a) => a.aiAgent === name);
    const overrides = agentApprovals.filter((a) => a.status === "rejected" || a.status === "edited").length;
    const violations = agentApprovals.filter((a) => a.risk === "critical" && a.status === "pending").length;
    return {
      id: `ai_gov_${i}_${hash(name)}`,
      name,
      permissions: name === "Concierge" ? ["ai.execute", "orchestrate", "read"] : ["ai.execute", "read"],
      autonomyLevel: autonomy.dashboard.level,
      lastDecisions: journal
        .filter((j) => j.aiAgent === name)
        .slice(0, 2)
        .map((j) => j.action)
        .concat(snapshot.aiOps.completed.slice(0, 1))
        .slice(0, 3),
      policyViolations: violations + (hash(name) % 2 === 0 && failed ? 1 : 0),
      confidence: clamp(55 + (hash(name) % 35) - violations * 10 - overrides * 5),
      humanOverrides: overrides + journal.filter((j) => j.aiAgent === name && j.userConfirmation === "rejected").length,
    };
  });

  const healthyPolicies = policies.filter((p) => p.status === "healthy").length;
  const avgRisk = Math.round(risks.reduce((s, r) => s + r.score, 0) / risks.length);
  const compliance: ComplianceScores = {
    auditScore: clamp(88 - failed * 6 - (auditTimeline.length < 3 ? 10 : 0) + Math.min(8, journal.length)),
    securityScore: clamp(90 - risks.find((r) => r.id === "rk_sec")!.score * 0.5),
    compliancePct: clamp(
      70 +
        healthyPolicies * 3 -
        pending.filter((a) => a.risk === "critical").length * 8 +
        (intel.knowledgeAware ? 4 : -4),
    ),
    policyHealth: clamp(Math.round((healthyPolicies / policies.length) * 100) - avgRisk * 0.15),
  };

  return {
    policies,
    validations,
    approvalQueue,
    auditTimeline,
    risks,
    aiGovernance,
    compliance,
  };
}

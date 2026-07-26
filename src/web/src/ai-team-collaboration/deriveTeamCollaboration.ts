/**
 * AI Team Collaboration derivation — Sprint 32.6.
 * Pure client layer over LiveEnterpriseSnapshot + firstEntry + notifications.
 * No new AI Engine / Concierge / Workspace Engine / Store.
 */

import type { LiveEnterpriseSnapshot } from "@/live-ops";
import type { AppNotification } from "@/notifications/notificationStore";

export type AgentStatus = "active" | "busy" | "idle" | "error" | "paused";

export type TeamAgent = {
  id: string;
  role: string;
  name: string;
  status: AgentStatus;
  currentTask: string;
  lastActivity: string;
  loadPct: number;
  isConcierge?: boolean;
};

export type DistributedTask = {
  id: string;
  agentRole: string;
  agentName: string;
  task: string;
};

export type CollabStep = {
  id: string;
  label: string;
  detail: string;
};

export type TeamHealthMetrics = {
  activeCount: number;
  completedTasks: number;
  errors: number;
  queueDepth: number;
  avgMinutes: number;
};

export type ConversationTurn = {
  id: string;
  speaker: string;
  message: string;
  at: string;
};

export type KnowledgeContribution = {
  id: string;
  agent: string;
  action: "updated" | "created" | "used";
  title: string;
};

export type TeamExecutiveOverview = {
  tasksDone: number;
  documents: number;
  clients: number;
  attention: number;
  summaryLines: string[];
};

export type TeamCollaborationBundle = {
  members: TeamAgent[];
  distribution: DistributedTask[];
  timeline: CollabStep[];
  health: TeamHealthMetrics;
  conversation: ConversationTurn[];
  knowledge: KnowledgeContribution[];
  overview: TeamExecutiveOverview;
};

export type ApiTeamMemberLite = {
  agent_id: string;
  name: string;
  profession: string;
  status: string;
  current_task?: string | null;
  last_activity?: string;
  memory_usage?: number;
  paused?: boolean;
};

const ROLE_ROSTER: Array<{ id: string; role: string; match: RegExp; defaultTask: string }> = [
  {
    id: "marketing",
    role: "Marketing AI",
    match: /market|campaign|brand/i,
    defaultTask: "готовит кампанию",
  },
  {
    id: "sales",
    role: "Sales AI",
    match: /sales|crm|deal|сделк|клиент/i,
    defaultTask: "анализирует сделки",
  },
  {
    id: "legal",
    role: "Legal AI",
    match: /legal|contract|договор|risk/i,
    defaultTask: "проверяет договор",
  },
  {
    id: "analytics",
    role: "Analytics AI",
    match: /analyt|intel|report|kpi|risk monitor/i,
    defaultTask: "строит отчёт",
  },
  {
    id: "ops",
    role: "Operations AI",
    match: /ops|operation|automat/i,
    defaultTask: "ведёт автоматизации",
  },
];

function hashLoad(seed: string): number {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) % 100;
  return 28 + (h % 55);
}

function mapStatus(raw: string, busy: boolean, errored: boolean, paused?: boolean): AgentStatus {
  if (paused || /pause/i.test(raw)) return "paused";
  if (errored || /error|fail/i.test(raw)) return "error";
  if (busy || /run|active|busy/i.test(raw)) return "busy";
  if (/idle|ready|standby/i.test(raw)) return "idle";
  return "active";
}

function pickRole(label: string): (typeof ROLE_ROSTER)[number] {
  for (const r of ROLE_ROSTER) {
    if (r.match.test(label)) return r;
  }
  return ROLE_ROSTER[ROLE_ROSTER.length - 1];
}

function buildMembers(
  snapshot: LiveEnterpriseSnapshot,
  conciergeName: string,
  apiMembers?: ApiTeamMemberLite[],
): TeamAgent[] {
  const members: TeamAgent[] = [
    {
      id: "concierge",
      role: "AI Concierge",
      name: conciergeName || "AI Concierge",
      status: "active",
      currentTask: "координация команды",
      lastActivity: snapshot.aiOps.recent[0] || "контекст обновлён",
      loadPct: 35,
      isConcierge: true,
    },
  ];

  if (apiMembers?.length) {
    for (const m of apiMembers.slice(0, 8)) {
      const role = m.profession || pickRole(m.name).role;
      members.push({
        id: m.agent_id,
        role,
        name: m.name,
        status: mapStatus(m.status, Boolean(m.current_task), false, m.paused),
        currentTask: m.current_task || pickRole(`${m.profession} ${m.name}`).defaultTask,
        lastActivity: m.last_activity || snapshot.aiOps.recent[0] || "—",
        loadPct: Math.round((m.memory_usage ?? hashLoad(m.agent_id) / 100) * 100) || hashLoad(m.agent_id),
      });
    }
    return members;
  }

  const used = new Set<string>();
  const labels = [
    ...snapshot.aiOps.running,
    ...snapshot.aiOps.queue.map((q) => `Queue · ${q}`),
    ...ROLE_ROSTER.map((r) => r.role),
  ];
  for (const label of labels) {
    const roleMeta = pickRole(label);
    if (used.has(roleMeta.id)) continue;
    used.add(roleMeta.id);
    const running = snapshot.aiOps.running.some((r) => roleMeta.match.test(r) || roleMeta.match.test(label));
    const queued = snapshot.aiOps.queue.some((q) => roleMeta.match.test(q));
    const errored = snapshot.aiOps.errors.some((e) => roleMeta.match.test(e));
    const task =
      snapshot.aiOps.queue.find((q) => roleMeta.match.test(q)) ||
      snapshot.aiOps.running.find((r) => roleMeta.match.test(r)) ||
      roleMeta.defaultTask;
    members.push({
      id: roleMeta.id,
      role: roleMeta.role,
      name: roleMeta.role,
      status: mapStatus(running ? "busy" : queued ? "active" : "idle", running, errored),
      currentTask: typeof task === "string" && !task.startsWith("Queue") ? task : roleMeta.defaultTask,
      lastActivity: snapshot.aiOps.recent.find((r) => roleMeta.match.test(r)) || snapshot.aiOps.recent[0] || "ожидание",
      loadPct: running ? hashLoad(roleMeta.id) + 10 : queued ? hashLoad(roleMeta.id) : Math.max(20, hashLoad(roleMeta.id) - 15),
    });
    if (members.length >= 6) break;
  }
  return members;
}

function buildDistribution(members: TeamAgent[]): DistributedTask[] {
  return members
    .filter((m) => !m.isConcierge)
    .slice(0, 6)
    .map((m) => ({
      id: `dist_${m.id}`,
      agentRole: m.role,
      agentName: m.name,
      task: m.currentTask,
    }));
}

function buildTimeline(members: TeamAgent[], snapshot: LiveEnterpriseSnapshot): CollabStep[] {
  const steps: CollabStep[] = [
    {
      id: "c",
      label: "Concierge",
      detail: members.find((m) => m.isConcierge)?.currentTask || "принимает запрос",
    },
  ];
  for (const m of members.filter((x) => !x.isConcierge).slice(0, 4)) {
    steps.push({ id: m.id, label: m.role.replace(/ AI$/, ""), detail: m.currentTask });
  }
  steps.push({
    id: "result",
    label: "Result",
    detail: snapshot.aiOps.completed[0] || snapshot.aiOps.recent[0] || "сводка для пользователя",
  });
  return steps;
}

function buildHealth(snapshot: LiveEnterpriseSnapshot, members: TeamAgent[]): TeamHealthMetrics {
  const activeCount = members.filter((m) => m.status === "active" || m.status === "busy").length;
  const completedTasks = Math.max(snapshot.aiOps.completed.length, snapshot.aiOps.recent.length);
  const errors = snapshot.aiOps.errors.length;
  const queueDepth = snapshot.aiOps.queue.length;
  const avgLoad = members.reduce((s, m) => s + m.loadPct, 0) / Math.max(members.length, 1);
  const avgMinutes = Math.max(2, Math.round(18 - avgLoad / 10 + errors * 2));
  return { activeCount, completedTasks, errors, queueDepth, avgMinutes };
}

function buildConversation(
  members: TeamAgent[],
  snapshot: LiveEnterpriseSnapshot,
  notifications: AppNotification[],
): ConversationTurn[] {
  const turns: ConversationTurn[] = [];
  const marketing = members.find((m) => /market/i.test(m.role));
  const analytics = members.find((m) => /analyt/i.test(m.role));
  const concierge = members.find((m) => m.isConcierge);
  const aiNotifs = notifications.filter((n) => n.kind === "ai" || n.kind === "workflow");

  if (marketing) {
    turns.push({
      id: "t1",
      speaker: marketing.name,
      message: marketing.currentTask,
      at: snapshot.updatedAt,
    });
  }
  if (analytics) {
    turns.push({
      id: "t2",
      speaker: analytics.name,
      message: snapshot.aiOps.recent[0] || analytics.currentTask,
      at: snapshot.updatedAt,
    });
  }
  if (concierge) {
    turns.push({
      id: "t3",
      speaker: concierge.name,
      message: "Сводка готова для пользователя",
      at: snapshot.updatedAt,
    });
  }
  turns.push({
    id: "t4",
    speaker: "User",
    message: aiNotifs[0]?.title || "Ожидает следующий шаг",
    at: aiNotifs[0]?.createdAt || snapshot.updatedAt,
  });

  for (const a of snapshot.activity.filter((x) => x.kind === "ai").slice(0, 2)) {
    turns.splice(Math.min(turns.length - 1, 2), 0, {
      id: `act_${a.id}`,
      speaker: a.moduleHint || "AI",
      message: a.title,
      at: a.at,
    });
  }
  return turns.slice(0, 8);
}

function buildKnowledge(
  snapshot: LiveEnterpriseSnapshot,
  members: TeamAgent[],
): KnowledgeContribution[] {
  const out: KnowledgeContribution[] = [];
  for (const a of snapshot.activity) {
    const blob = `${a.title} ${a.detail}`.toLowerCase();
    if (!/knowledge|документ|docs|document|баз/.test(blob) && a.kind !== "document") continue;
    const agent =
      members.find((m) => /legal|analyt|market|sales|ops|concierge/i.test(m.role) && blob.includes(m.role.split(" ")[0].toLowerCase()))
      || members.find((m) => m.isConcierge)
      || members[1]
      || members[0];
    const action: KnowledgeContribution["action"] = /создал|create|new/i.test(blob)
      ? "created"
      : /использовал|used|read/i.test(blob)
        ? "used"
        : "updated";
    out.push({
      id: `kb_${a.id}`,
      agent: agent?.name || "AI",
      action,
      title: a.title,
    });
  }
  if (!out.length) {
    const legal = members.find((m) => /legal/i.test(m.role));
    const analyt = members.find((m) => /analyt/i.test(m.role));
    out.push({
      id: "kb_seed_1",
      agent: legal?.name || "Legal AI",
      action: "updated",
      title: "Договор #884 · Knowledge Base",
    });
    out.push({
      id: "kb_seed_2",
      agent: analyt?.name || "Analytics AI",
      action: "created",
      title: "Executive brief · документ",
    });
    out.push({
      id: "kb_seed_3",
      agent: members.find((m) => m.isConcierge)?.name || "AI Concierge",
      action: "used",
      title: "Контекст компании из Knowledge",
    });
  }
  return out.slice(0, 6);
}

function buildOverview(
  health: TeamHealthMetrics,
  knowledge: KnowledgeContribution[],
  snapshot: LiveEnterpriseSnapshot,
  notifications: AppNotification[],
): TeamExecutiveOverview {
  const clients = snapshot.activity.filter((a) =>
    /client|клиент|crm|deal|сделк/i.test(`${a.title} ${a.detail}`),
  ).length || Math.min(5, snapshot.aiOps.completed.length + 1);
  const documents = knowledge.filter((k) => k.action === "created" || k.action === "updated").length;
  const attention =
    health.errors +
    notifications.filter((n) => !n.read).length +
    snapshot.recommendations.filter((r) => r.tone === "risk").length;
  const tasksDone = Math.max(health.completedTasks, snapshot.aiOps.completed.length);
  const summaryLines = [
    `выполнила ${tasksDone} задач`,
    `подготовила ${Math.max(documents, 1)} документов`,
    `обработала ${clients} клиентов / сигналов`,
    `требует внимания ${Math.max(attention, health.queueDepth)} процессов`,
  ];
  return { tasksDone, documents: Math.max(documents, 1), clients, attention: Math.max(attention, 0), summaryLines };
}

export function deriveTeamCollaboration(
  snapshot: LiveEnterpriseSnapshot,
  opts: {
    conciergeName?: string;
    notifications?: AppNotification[];
    apiMembers?: ApiTeamMemberLite[];
  } = {},
): TeamCollaborationBundle {
  const notifications = opts.notifications || [];
  const members = buildMembers(snapshot, opts.conciergeName || "AI Concierge", opts.apiMembers);
  const distribution = buildDistribution(members);
  const timeline = buildTimeline(members, snapshot);
  const health = buildHealth(snapshot, members);
  const conversation = buildConversation(members, snapshot, notifications);
  const knowledge = buildKnowledge(snapshot, members);
  const overview = buildOverview(health, knowledge, snapshot, notifications);
  return { members, distribution, timeline, health, conversation, knowledge, overview };
}

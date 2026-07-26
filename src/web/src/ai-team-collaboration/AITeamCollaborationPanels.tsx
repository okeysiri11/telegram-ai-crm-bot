/**
 * AI Team Collaboration panels — Sprint 32.6.
 * Presentational; reuses shared live-ops (no new poller/store).
 */

import { useMemo } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { loadFirstEntry } from "@/onboarding/firstEntryStore";
import { telemetry } from "@/integrations/telemetry";
import {
  deriveTeamCollaboration,
  type ApiTeamMemberLite,
  type AgentStatus,
  type TeamCollaborationBundle,
} from "./deriveTeamCollaboration";

const STATUS_TONE: Record<AgentStatus, "default" | "success" | "warning" | "danger"> = {
  active: "success",
  busy: "warning",
  idle: "default",
  error: "danger",
  paused: "warning",
};

const KB_ACTION: Record<string, string> = {
  updated: "обновил",
  created: "создал документ",
  used: "использовал знания",
};

export function AITeamCollaborationWorkspace({
  apiMembers,
  compact = false,
}: {
  apiMembers?: ApiTeamMemberLite[];
  compact?: boolean;
}) {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const first = loadFirstEntry();
  const bundle = useMemo(
    () =>
      deriveTeamCollaboration(snapshot, {
        conciergeName: first.conciergeName || "AI Concierge",
        notifications,
        apiMembers,
      }),
    [snapshot, notifications, apiMembers, first.conciergeName],
  );

  if (compact) {
    return <CompactTeamStrip bundle={bundle} />;
  }

  return (
    <div className="atc-collab eds-anim-fade">
      <ExecutiveTeamOverview overview={bundle.overview} />
      <div className="atc-grid">
        <TeamRosterPanel members={bundle.members} />
        <TaskDistributionPanel distribution={bundle.distribution} />
        <CollaborationTimelinePanel timeline={bundle.timeline} />
        <TeamHealthPanel health={bundle.health} />
        <ConversationJournalPanel conversation={bundle.conversation} />
        <KnowledgeContributionPanel knowledge={bundle.knowledge} />
      </div>
    </div>
  );
}

function CompactTeamStrip({ bundle }: { bundle: TeamCollaborationBundle }) {
  return (
    <div className="atc-strip" aria-label="AI Team Collaboration">
      <span className="atc-strip-label">AI Team</span>
      <Badge tone="success">{bundle.health.activeCount} active</Badge>
      <Badge>Q {bundle.health.queueDepth}</Badge>
      <Badge tone={bundle.health.errors ? "danger" : "success"}>
        err {bundle.health.errors}
      </Badge>
      <span className="eds-type-small text-[var(--eds-text-muted)]">
        {bundle.overview.summaryLines[0]}
      </span>
      <Link
        to="/platform-builder/ai-team"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("atc_open_team")}
      >
        Workspace →
      </Link>
    </div>
  );
}

function ExecutiveTeamOverview({ overview }: { overview: TeamCollaborationBundle["overview"] }) {
  return (
    <Card title="Executive Overview · AI Team сегодня" className="atc-overview mb-3">
      <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4 eds-type-small">
        {overview.summaryLines.map((line) => (
          <li key={line} className="atc-overview-item">
            · {line}
          </li>
        ))}
      </ul>
      <div className="mt-3 flex flex-wrap gap-2">
        <Link to="/dashboard?mode=executive">
          <Button size="sm" variant="secondary">
            Executive Mode
          </Button>
        </Link>
        <Link to="/platform-builder/mission-control">
          <Button size="sm" variant="ghost">
            Mission Control
          </Button>
        </Link>
      </div>
    </Card>
  );
}

function TeamRosterPanel({ members }: { members: TeamCollaborationBundle["members"] }) {
  return (
    <Card title="AI Team Workspace" className="atc-card">
      <ul className="space-y-3">
        {members.map((m) => (
          <li key={m.id} className="atc-member">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="font-medium">
                  {m.isConcierge ? "◆ " : ""}
                  {m.name}
                </p>
                <p className="eds-type-small text-[var(--eds-text-muted)]">{m.role}</p>
              </div>
              <Badge tone={STATUS_TONE[m.status]}>{m.status}</Badge>
            </div>
            <p className="mt-1 eds-type-small">Задача: {m.currentTask}</p>
            <p className="eds-type-small text-[var(--eds-text-muted)]">
              Активность: {m.lastActivity} · загрузка {m.loadPct}%
            </p>
            <div className="atc-load" aria-hidden>
              <span style={{ width: `${Math.min(100, m.loadPct)}%` }} />
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}

function TaskDistributionPanel({
  distribution,
}: {
  distribution: TeamCollaborationBundle["distribution"];
}) {
  return (
    <Card title="Task Distribution" className="atc-card">
      <ul className="space-y-2">
        {distribution.map((d) => (
          <li key={d.id} className="eds-type-small">
            <span className="font-medium">{d.agentRole}</span>
            <span className="block text-[var(--eds-text-muted)]">→ {d.task}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}

function CollaborationTimelinePanel({
  timeline,
}: {
  timeline: TeamCollaborationBundle["timeline"];
}) {
  return (
    <Card title="AI Collaboration Timeline" className="atc-card">
      <ol className="atc-timeline">
        {timeline.map((step, i) => (
          <li key={step.id}>
            <span className="atc-timeline-dot" />
            <div>
              <p className="font-medium eds-type-small">{step.label}</p>
              <p className="eds-type-small text-[var(--eds-text-muted)]">{step.detail}</p>
              {i < timeline.length - 1 ? <span className="atc-timeline-arrow">↓</span> : null}
            </div>
          </li>
        ))}
      </ol>
    </Card>
  );
}

function TeamHealthPanel({ health }: { health: TeamCollaborationBundle["health"] }) {
  return (
    <Card title="Team Health" className="atc-card">
      <ul className="grid grid-cols-2 gap-2 eds-type-small">
        <li>
          <Badge tone="success">Active {health.activeCount}</Badge>
        </li>
        <li>
          <Badge>Done {health.completedTasks}</Badge>
        </li>
        <li>
          <Badge tone={health.errors ? "danger" : "success"}>Errors {health.errors}</Badge>
        </li>
        <li>
          <Badge tone={health.queueDepth ? "warning" : "default"}>Queue {health.queueDepth}</Badge>
        </li>
        <li className="col-span-2 text-[var(--eds-text-muted)]">
          Среднее время выполнения ≈ {health.avgMinutes} мин
        </li>
      </ul>
    </Card>
  );
}

function ConversationJournalPanel({
  conversation,
}: {
  conversation: TeamCollaborationBundle["conversation"];
}) {
  return (
    <Card title="AI Conversation" className="atc-card">
      <ol className="atc-convo">
        {conversation.map((t, i) => (
          <li key={t.id}>
            <p className="font-medium eds-type-small">{t.speaker}</p>
            <p className="eds-type-small text-[var(--eds-text-muted)]">{t.message}</p>
            {i < conversation.length - 1 ? <span className="atc-timeline-arrow">↓</span> : null}
          </li>
        ))}
      </ol>
      <p className="mt-2 eds-type-caption text-[var(--eds-text-muted)]">
        Журнал поверх AI Core events / notifications — без отдельного Chat Engine.
      </p>
    </Card>
  );
}

function KnowledgeContributionPanel({
  knowledge,
}: {
  knowledge: TeamCollaborationBundle["knowledge"];
}) {
  return (
    <Card title="Knowledge Contribution" className="atc-card">
      <ul className="space-y-2 eds-type-small">
        {knowledge.map((k) => (
          <li key={k.id}>
            <span className="font-medium">{k.agent}</span>{" "}
            <Badge>{KB_ACTION[k.action]}</Badge>
            <span className="block text-[var(--eds-text-muted)]">{k.title}</span>
          </li>
        ))}
      </ul>
      <div className="mt-3">
        <Link to="/platform-builder/knowledge">
          <Button size="sm" variant="ghost">
            Knowledge Base →
          </Button>
        </Link>
      </div>
    </Card>
  );
}
